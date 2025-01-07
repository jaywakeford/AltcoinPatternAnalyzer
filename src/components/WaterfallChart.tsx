import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { MarketData } from '../services/DataService';

interface WaterfallChartProps {
  data: MarketData[];
  selectedCohort: string;
  onSequenceSelect: (sequence: string[]) => void;
}

const WaterfallChart: React.FC<WaterfallChartProps> = ({ data, selectedCohort, onSequenceSelect }) => {
  const chartRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!data.length || !chartRef.current) return;

    const svg = d3.select(chartRef.current);
    const margin = { top: 20, right: 30, bottom: 40, left: 60 };
    const width = 800 - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;

    // Clear previous content
    svg.selectAll("*").remove();

    const g = svg
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Create scales
    const xScale = d3.scaleTime()
      .domain(d3.extent(data, d => new Date(d.timestamp)) as [Date, Date])
      .range([0, width]);

    const yScale = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.price) as number])
      .range([height, 0]);

    // Create axes
    const xAxis = d3.axisBottom(xScale);
    const yAxis = d3.axisLeft(yScale);

    // Add axes to chart
    g.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(xAxis);

    g.append("g")
      .call(yAxis);

    // Add line path
    const line = d3.line<MarketData>()
      .x(d => xScale(new Date(d.timestamp)))
      .y(d => yScale(d.price));

    g.append("path")
      .datum(data)
      .attr("fill", "none")
      .attr("stroke", "steelblue")
      .attr("stroke-width", 1.5)
      .attr("d", line);

    // Add interactive overlay
    const overlay = g.append("rect")
      .attr("class", "overlay")
      .attr("width", width)
      .attr("height", height)
      .style("opacity", 0);

    // Add tooltip
    const tooltip = d3.select("body").append("div")
      .attr("class", "tooltip")
      .style("opacity", 0);

    overlay
      .on("mousemove", function(event) {
        const [x] = d3.pointer(event);
        const bisect = d3.bisector((d: MarketData) => new Date(d.timestamp)).left;
        const x0 = xScale.invert(x);
        const i = bisect(data, x0, 1);
        const d0 = data[i - 1];
        const d1 = data[i];
        const d = x0.getTime() - d0.timestamp > d1.timestamp - x0.getTime() ? d1 : d0;

        tooltip
          .style("opacity", 0.9)
          .html(`Price: $${d.price.toFixed(2)}<br/>Time: ${new Date(d.timestamp).toLocaleString()}`)
          .style("left", (event.pageX + 10) + "px")
          .style("top", (event.pageY - 28) + "px");
      })
      .on("mouseout", function() {
        tooltip.style("opacity", 0);
      });

  }, [data, selectedCohort]);

  return (
    <div className="waterfall-chart">
      <svg
        ref={chartRef}
        width={800}
        height={400}
        style={{ maxWidth: '100%', height: 'auto' }}
      />
    </div>
  );
};

export default WaterfallChart; 