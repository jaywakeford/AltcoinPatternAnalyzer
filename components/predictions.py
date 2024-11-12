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
    
    # Prediction settings
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
    
    if not data.empty and len(selected_models) > 0:
        try:
            # Generate predictions
            predictor = PricePredictor()
            predictions = predictor.predict(data, forecast_days)
            
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
            st.info("Please try adjusting the parameters or selecting different models.")
    else:
        st.warning("Please select at least one prediction model and ensure data is available.")
