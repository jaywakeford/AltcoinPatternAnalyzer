import React, { useEffect, useRef } from 'react';
import { MarketData } from '../services/DataService';
import * as d3 from 'd3';

interface WaterfallChartProps {
  data: MarketData[];
  selectedCohort: string;
  onSequenceSelect: (sequence: string[]) => void;
}

interface DataPoint extends MarketData {
  timestamp: number;
  marketCap: number;
}

const WaterfallChart: React.FC<WaterfallChartProps> = ({
  data,
  selectedCohort,
  onSequenceSelect
}: WaterfallChartProps) => {
  const chartRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    console.log('WaterfallChart mounted', { data, chartRef: chartRef.current });
    
    if (!chartRef.current || !data.length) {
      console.log('Missing ref or data', { hasRef: !!chartRef.current, dataLength: data.length });
      return;
    }

    // Clear previous chart
    d3.select(chartRef.current).selectAll('*').remove();

    try {
      // Chart dimensions
      const margin = { top: 40, right: 80, bottom: 60, left: 80 };
      const width = 1000 - margin.left - margin.right;
      const height = 500 - margin.top - margin.bottom;

      console.log('Creating chart with dimensions:', { width, height, margin });

      // Create SVG
      const svg = d3.select(chartRef.current)
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

      // Create tooltip
      const tooltip = d3.select(tooltipRef.current)
        .style('opacity', 0)
        .attr('class', 'tooltip');

      // Format functions
      const formatDate = d3.timeFormat("%b %d, %Y");
      const formatValue = d3.format(",.2f");
      const formatMarketCap = (value: number) => `$${d3.format(".2s")(value)}`;

      // Create scales
      const xScale = d3.scaleTime()
        .domain(d3.extent(data, (d: DataPoint) => new Date(d.timestamp)) as [Date, Date])
        .range([0, width]);

      const yScale = d3.scaleLinear()
        .domain([0, d3.max(data, (d: DataPoint) => d.marketCap) || 0])
        .range([height, 0])
        .nice();

      // Add grid lines
      svg.append('g')
        .attr('class', 'grid-lines')
        .selectAll('line')
        .data(yScale.ticks())
        .enter()
        .append('line')
        .attr('x1', 0)
        .attr('x2', width)
        .attr('y1', d => yScale(d))
        .attr('y2', d => yScale(d))
        .attr('stroke', '#e0e0e0')
        .attr('stroke-dasharray', '2,2');

      // Create axes
      const xAxis = d3.axisBottom(xScale)
        .ticks(7)
        .tickFormat(d => formatDate(d as Date));

      const yAxis = d3.axisLeft(yScale)
        .ticks(8)
        .tickFormat(d => formatMarketCap(d as number));

      // Add axes
      svg.append('g')
        .attr('class', 'x-axis')
        .attr('transform', `translate(0,${height})`)
        .call(xAxis)
        .selectAll('text')
        .style('text-anchor', 'end')
        .attr('dx', '-.8em')
        .attr('dy', '.15em')
        .attr('transform', 'rotate(-45)');

      svg.append('g')
        .attr('class', 'y-axis')
        .call(yAxis);

      // Add axis labels
      svg.append('text')
        .attr('class', 'x-label')
        .attr('text-anchor', 'middle')
        .attr('x', width / 2)
        .attr('y', height + margin.bottom - 5)
        .text('Date');

      svg.append('text')
        .attr('class', 'y-label')
        .attr('text-anchor', 'middle')
        .attr('transform', 'rotate(-90)')
        .attr('x', -height / 2)
        .attr('y', -margin.left + 20)
        .text('Market Cap (USD)');

      // Add lines
      const line = d3.line<DataPoint>()
        .x(d => xScale(new Date(d.timestamp)))
        .y(d => yScale(d.marketCap))
        .curve(d3.curveMonotoneX);

      // Add area under the line
      const area = d3.area<DataPoint>()
        .x(d => xScale(new Date(d.timestamp)))
        .y0(height)
        .y1(d => yScale(d.marketCap))
        .curve(d3.curveMonotoneX);

      // Add area with gradient
      const gradient = svg.append('defs')
        .append('linearGradient')
        .attr('id', 'area-gradient')
        .attr('x1', '0%')
        .attr('y1', '0%')
        .attr('x2', '0%')
        .attr('y2', '100%');

      gradient.append('stop')
        .attr('offset', '0%')
        .attr('stop-color', 'var(--chart-color)')
        .attr('stop-opacity', 0.3);

      gradient.append('stop')
        .attr('offset', '100%')
        .attr('stop-color', 'var(--chart-color)')
        .attr('stop-opacity', 0.05);

      svg.append('path')
        .datum(data)
        .attr('class', 'area')
        .attr('d', area)
        .attr('fill', 'url(#area-gradient)');

      svg.append('path')
        .datum(data)
        .attr('class', 'line')
        .attr('d', line);

      // Add data points with hover effects
      const dots = svg.selectAll('.dot')
        .data(data)
        .enter()
        .append('circle')
        .attr('class', 'dot')
        .attr('cx', d => xScale(new Date(d.timestamp)))
        .attr('cy', d => yScale(d.marketCap))
        .attr('r', 5);

      // Add hover effects
      dots.on('mouseover', function(event, d: DataPoint) {
        const [x, y] = d3.pointer(event);
        
        d3.select(this)
          .transition()
          .duration(200)
          .attr('r', 8);

        tooltip
          .style('opacity', 1)
          .html(`
            <div class="tooltip-content">
              <div class="tooltip-date">${formatDate(new Date(d.timestamp))}</div>
              <div class="tooltip-value">Market Cap: ${formatMarketCap(d.marketCap)}</div>
              <div class="tooltip-price">Price: $${formatValue(d.price)}</div>
              <div class="tooltip-volume">Volume: ${formatMarketCap(d.volume24h)}</div>
            </div>
          `)
          .style('left', (x + margin.left + 10) + 'px')
          .style('top', (y + margin.top - 10) + 'px');
      })
      .on('mouseout', function() {
        d3.select(this)
          .transition()
          .duration(200)
          .attr('r', 5);

        tooltip.style('opacity', 0);
      });

      // Add chart title
      svg.append('text')
        .attr('class', 'chart-title')
        .attr('x', width / 2)
        .attr('y', -margin.top / 2)
        .attr('text-anchor', 'middle')
        .style('font-size', '16px')
        .style('font-weight', 'bold')
        .text('Bitcoin Market Cap Over Time');

      console.log('Chart rendering complete');
    } catch (error) {
      console.error('Error rendering chart:', error);
    }
  }, [data, selectedCohort, onSequenceSelect]);

  return (
    <div className="waterfall-chart-container">
      <div className="waterfall-chart" style={{ width: '100%', height: '600px', minHeight: '500px' }}>
        <svg ref={chartRef} style={{ width: '100%', height: '100%' }}></svg>
        <div ref={tooltipRef} className="tooltip"></div>
      </div>
    </div>
  );
};

export default WaterfallChart; 