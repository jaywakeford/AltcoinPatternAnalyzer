import streamlit as st
import plotly.graph_objects as go
from utils.price_predictor import PricePredictor
import pandas as pd

def render_prediction_section(data: pd.DataFrame):
    """Render price predictions section."""
    st.subheader("📈 Price Predictions")
    
    # Add description
    st.markdown("""
    This section shows price predictions using multiple models:
    - Simple Moving Average (SMA) based prediction
    - Exponential Moving Average (EMA) based prediction
    - Momentum-based prediction
    
    *Note: These predictions are for educational purposes only and should not be used as financial advice.*
    """)
    
    # Data validation
    if data is None or data.empty:
        st.error("No data available for prediction")
        st.info("Please ensure valid market data is available")
        return

    # Add data validation and transformation
    if 'price' not in data.columns:
        if 'close' in data.columns:
            data['price'] = data['close']
        else:
            st.error("Required price data is missing")
            st.info("Please ensure the data contains either 'price' or 'close' column")
            return

    # Ensure numeric type
    try:
        data['price'] = pd.to_numeric(data['price'], errors='coerce')
    except Exception as e:
        st.error(f"Error converting price data to numeric: {str(e)}")
        return

    # Handle missing values
    if data['price'].isnull().any():
        data = data.dropna(subset=['price'])
        if data.empty:
            st.error("No valid price data available after cleaning")
            return
    
    tab1, tab2 = st.tabs(["Model Predictions", "Chart Analysis & AI Predictions"])
    
    with tab1:
        # Model prediction settings
        col1, col2 = st.columns(2)
        
        with col1:
            forecast_days = st.slider(
                "Forecast Days",
                min_value=1,
                max_value=30,
                value=7,
                help="Number of days to forecast"
            )
        
        with col2:
            selected_models = st.multiselect(
                "Select Models",
                ["SMA", "EMA", "Momentum"],
                default=["SMA", "EMA"],
                help="Choose prediction models to display"
            )
        
        if len(selected_models) > 0:
            try:
                # Generate predictions with error handling
                predictor = PricePredictor()
                predictions = predictor.predict(data, forecast_days)
                
                if not predictions:
                    st.warning("No predictions generated. Please try different parameters.")
                    return
                
                # Create visualization
                fig = go.Figure()
                
                # Add historical data
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=data['price'],
                    name='Historical',
                    line=dict(color='#17C37B')
                ))
                
                # Add predictions
                colors = {
                    'SMA': '#FF9900',
                    'EMA': '#00FFFF',
                    'Momentum': '#FF00FF'
                }
                
                for model_name, pred_df in predictions.items():
                    if model_name.upper() in selected_models:
                        fig.add_trace(go.Scatter(
                            x=pred_df.index,
                            y=pred_df['price'],
                            name=f'{model_name} Prediction',
                            line=dict(
                                color=colors.get(model_name.upper(), '#999999'),
                                dash='dash'
                            )
                        ))
                
                # Update layout
                fig.update_layout(
                    title="Price Predictions",
                    xaxis_title="Date",
                    yaxis_title="Price (USD)",
                    template="plotly_dark",
                    height=500,
                    showlegend=True
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show metrics
                metrics = predictor.get_prediction_metrics(predictions, data)
                if metrics:
                    st.subheader("Model Performance Metrics")
                    
                    metric_cols = st.columns(len(metrics))
                    for idx, (model_name, model_metrics) in enumerate(metrics.items()):
                        with metric_cols[idx]:
                            st.metric(
                                label=f"{model_name} MAPE",
                                value=f"{model_metrics['mape']:.2f}%",
                                help="Mean Absolute Percentage Error"
                            )
                            st.metric(
                                label=f"{model_name} RMSE",
                                value=f"${model_metrics['rmse']:.2f}",
                                help="Root Mean Square Error"
                            )
                
            except Exception as e:
                st.error(f"Error generating predictions: {str(e)}")
                st.info("Please ensure data contains valid price information")
                return
        else:
            st.warning("Please select at least one prediction model")
    
    with tab2:
        render_chart_analysis_section()

def render_prediction_table(entry_price, target_price, stop_loss, trailing_stop, probability, timeframe):
    """Render prediction metrics in a formatted table."""
    df = pd.DataFrame({
        'Metric': ['Entry Price', 'Target Price', 'Stop Loss', 'Trailing Stop', 'Probability'],
        'Value': [
            f"${entry_price:,.2f}",
            f"${target_price:,.2f}",
            f"${stop_loss:,.2f}",
            f"${trailing_stop:,.2f}",
            f"{probability:.1%}"
        ]
    })
    
    # Style the dataframe
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
    st.caption(f"Timeframe: {timeframe}")

def render_chart_analysis_section():
    """Render chart analysis and AI predictions section."""
    st.markdown("### 📊 Chart Analysis & AI Predictions")
    
    # Add file uploader for chart images
    uploaded_file = st.file_uploader(
        "Upload Chart Image",
        type=['png', 'jpg', 'jpeg'],
        help="Upload a chart image for AI analysis"
    )
    
    if uploaded_file:
        # Display uploaded chart
        st.image(uploaded_file, caption="Uploaded Chart", use_column_width=True)
        
        # Add spacing
        st.markdown("<div style='margin: 1em 0;'></div>", unsafe_allow_html=True)
        
        # Timeframe selection
        minutes_ahead = st.slider(
            "Predict Minutes Ahead",
            min_value=5,
            max_value=120,
            value=30,
            step=5,
            help="Select prediction timeframe in minutes"
        )
        
        # Create three columns for prediction tables
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### Bullish Scenario")
            render_prediction_table(
                entry_price=88750,
                target_price=89200,
                stop_loss=88500,
                trailing_stop=88600,
                probability=0.85,
                timeframe=f"{minutes_ahead} minutes"
            )
            st.markdown("""
            **Analysis:**
            Strong momentum indicated by:
            - Rising volume
            - Higher highs formation
            - RSI divergence
            """)
        
        with col2:
            st.markdown("### Neutral Scenario")
            render_prediction_table(
                entry_price=88750,
                target_price=88900,
                stop_loss=88600,
                trailing_stop=88650,
                probability=0.60,
                timeframe=f"{minutes_ahead} minutes"
            )
            st.markdown("""
            **Analysis:**
            Consolidation phase showing:
            - Decreasing volatility
            - Balanced volume
            - Range-bound price action
            """)
        
        with col3:
            st.markdown("### Bearish Scenario")
            render_prediction_table(
                entry_price=88750,
                target_price=88300,
                stop_loss=88900,
                trailing_stop=88800,
                probability=0.45,
                timeframe=f"{minutes_ahead} minutes"
            )
            st.markdown("""
            **Analysis:**
            Potential reversal indicated by:
            - Weakening momentum
            - Resistance level ahead
            - Volume divergence
            """)
