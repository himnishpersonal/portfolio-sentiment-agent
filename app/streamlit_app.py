"""
Streamlit interface for Portfolio Sentiment Intelligence Agent.

Users can:
1. Register with their email
2. Add/manage stock tickers in their portfolio
3. View portfolio status
4. Trigger manual sentiment analysis
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import db_manager, User, Portfolio, PipelineRun
from services.portfolio_manager import PortfolioManager
from sqlalchemy import desc

# Page configuration
st.set_page_config(
    page_title="Portfolio Sentiment Agent",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional dark theme
st.markdown("""
<style>
    /* Professional dark color scheme */
    :root {
        --primary: #3b82f6;
        --primary-dark: #2563eb;
        --secondary: #64748b;
        --accent: #0ea5e9;
        --success: #10b981;
        --warning: #f59e0b;
        --error: #ef4444;
        --bg-dark: #0f172a;
        --bg-card: #1e293b;
        --bg-hover: #334155;
        --text-primary: #f1f5f9;
        --text-secondary: #cbd5e1;
        --border: #334155;
    }
    
    /* Main theme - dark background */
    .stApp {
        background: #0f172a;
        color: #f1f5f9;
    }
    
    /* Header styling - professional typography */
    .main-header {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        color: #f1f5f9;
        text-align: center;
        padding: 1.5rem 0;
        margin-bottom: 0.5rem;
        border-bottom: 3px solid #3b82f6;
    }
    
    .sub-header {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
        color: #cbd5e1;
        text-align: center;
        margin-bottom: 2rem;
        font-size: 1.1rem;
    }
    
    /* Card styling - dark cards */
    .metric-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #3b82f6;
    }
    
    .metric-label {
        color: #cbd5e1;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    
    /* Table styling */
    .portfolio-table {
        background: #1e293b;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #334155;
    }
    
    /* Button styling - professional blue */
    .stButton > button {
        background: #3b82f6;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.625rem 1.5rem;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background: #2563eb;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 6px;
        color: #f1f5f9;
    }
    
    .stNumberInput > div > div > input {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 6px;
        color: #f1f5f9;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: #1e293b;
        border-right: 1px solid #334155;
    }
    
    [data-testid="stSidebar"] * {
        color: #f1f5f9;
    }
    
    /* Success/Error messages */
    .success-msg {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid #10b981;
        border-radius: 6px;
        padding: 1rem;
        color: #6ee7b7;
    }
    
    .error-msg {
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid #ef4444;
        border-radius: 6px;
        padding: 1rem;
        color: #fca5a5;
    }
    
    /* Ticker badge */
    .ticker-badge {
        display: inline-block;
        background: #3b82f6;
        color: white;
        padding: 0.375rem 0.875rem;
        border-radius: 6px;
        font-weight: 600;
        margin: 0.25rem;
        font-size: 0.875rem;
    }
    
    /* Status indicators */
    .status-success {
        color: #10b981;
    }
    
    .status-pending {
        color: #f59e0b;
    }
    
    .status-failed {
        color: #ef4444;
    }
    
    /* Professional typography */
    h1, h2, h3, h4, h5, h6 {
        color: #f1f5f9;
        font-weight: 700;
    }
    
    p, span, div {
        color: #cbd5e1;
    }
    
    /* Clean table styling */
    .dataframe {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 6px;
        color: #f1f5f9;
    }
    
    /* Info boxes */
    .stAlert {
        border-radius: 6px;
        background: #1e293b;
        border: 1px solid #334155;
    }
    
    /* Text input labels */
    label {
        color: #cbd5e1 !important;
    }
    
    /* Selectbox and other inputs */
    .stSelectbox > div > div {
        background: #1e293b;
        border: 1px solid #334155;
        color: #f1f5f9;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #1e293b;
        border-bottom: 1px solid #334155;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #cbd5e1;
    }
    
    .stTabs [aria-selected="true"] {
        color: #3b82f6;
        border-bottom: 2px solid #3b82f6;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #f1f5f9;
    }
    
    [data-testid="stMetricLabel"] {
        color: #cbd5e1;
    }
    
    /* Dataframe styling */
    .stDataFrame {
        background: #1e293b;
    }
    
    /* Markdown text */
    .stMarkdown {
        color: #cbd5e1;
    }
    
    /* Divider */
    hr {
        border-color: #334155;
    }
    
    /* Code blocks */
    code {
        background: #1e293b;
        color: #3b82f6;
        border: 1px solid #334155;
    }
</style>
""", unsafe_allow_html=True)


def get_user_by_email(email: str) -> dict | None:
    """Get user by email.
    
    Returns:
        Dictionary with user data or None.
    """
    try:
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.email == email).first()
            if user:
                # Extract data while session is active
                return {"id": user.id, "email": user.email}
            return None
    except Exception:
        return None


def get_user_portfolio(user_id: int) -> dict:
    """Get user's portfolio."""
    try:
        return PortfolioManager.get_user_portfolio(user_id)
    except Exception:
        return {}


def get_recent_runs(user_id: int, limit: int = 5) -> list:
    """Get recent pipeline runs for user."""
    try:
        with db_manager.get_session() as session:
            runs = session.query(PipelineRun)\
                .filter(PipelineRun.user_id == user_id)\
                .order_by(desc(PipelineRun.started_at))\
                .limit(limit)\
                .all()
            return [
                {
                    "id": r.id,
                    "started_at": r.started_at,
                    "status": r.status,
                    "execution_time": r.execution_time_seconds
                }
                for r in runs
            ]
    except Exception:
        return []


def main():
    """Main Streamlit app."""
    
    # Header
    st.markdown('<h1 class="main-header">Portfolio Sentiment Agent</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-powered financial news sentiment analysis for your portfolio</p>', unsafe_allow_html=True)
    
    # Initialize session state
    if "user" not in st.session_state:
        st.session_state.user = None
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = {}
    
    # Sidebar - User Authentication
    with st.sidebar:
        st.markdown("### Account")
        
        if st.session_state.user is None:
            # Login/Register form
            email = st.text_input("Email Address", placeholder="your@email.com")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Login", use_container_width=True):
                    if email:
                        user = get_user_by_email(email)
                        if user:
                            st.session_state.user = user
                            st.session_state.portfolio = get_user_portfolio(user["id"])
                            st.success(f"Welcome back!")
                            st.rerun()
                        else:
                            st.error("User not found. Please register.")
                    else:
                        st.warning("Please enter your email.")
            
            with col2:
                if st.button("Register", use_container_width=True):
                    if email:
                        try:
                            # Check if user exists first
                            existing_user = get_user_by_email(email)
                            if existing_user:
                                st.error("Email already registered. Please use Login button.")
                            else:
                                # Create new user
                                with db_manager.get_session() as session:
                                    user = User(email=email)
                                    session.add(user)
                                    session.commit()
                                    session.refresh(user)
                                    user_data = {"id": user.id, "email": user.email}
                                
                                st.session_state.user = user_data
                                st.session_state.portfolio = {}
                                st.success("Account created successfully!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Registration failed: {e}")
                    else:
                        st.warning("Please enter your email.")
        else:
            # Logged in user info
            st.markdown(f"**Logged in as:**")
            st.markdown(f"**Email:** {st.session_state.user['email']}")
            st.markdown(f"**User ID:** {st.session_state.user['id']}")
            
            if st.button("Logout", use_container_width=True):
                st.session_state.user = None
                st.session_state.portfolio = {}
                st.rerun()
            
            st.markdown("---")
            
            # Quick stats
            portfolio_count = len(st.session_state.portfolio)
            st.metric("Portfolio Tickers", portfolio_count)
            
            if portfolio_count > 0:
                total_weight = sum(st.session_state.portfolio.values())
                st.metric("Total Weight", f"{total_weight:.1%}")
    
    # Main content
    if st.session_state.user is None:
        # Welcome screen for non-logged in users
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">News</div>
                <div class="metric-label">Daily News Analysis</div>
                <p style="color: #cbd5e1; margin-top: 0.5rem; font-size: 0.9rem;">
                    Automatically fetches and analyzes financial news for your stocks
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">AI</div>
                <div class="metric-label">AI-Powered Insights</div>
                <p style="color: #cbd5e1; margin-top: 0.5rem; font-size: 0.9rem;">
                    FinBERT sentiment analysis + LLM summaries
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">Reports</div>
                <div class="metric-label">Daily Email Reports</div>
                <p style="color: #cbd5e1; margin-top: 0.5rem; font-size: 0.9rem;">
                    Receive sentiment reports before market open
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.info("**Login or Register** in the sidebar to get started!")
        
    else:
        # Logged in user dashboard
        tabs = st.tabs(["Dashboard", "Add Stocks", "Settings"])
        
        # Dashboard Tab
        with tabs[0]:
            st.markdown("### Your Portfolio")
            
            if st.session_state.portfolio:
                # Portfolio table with delete buttons
                portfolio_items = sorted(
                    st.session_state.portfolio.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Create portfolio display with delete buttons
                    st.markdown("#### Portfolio Holdings")
                    
                    # Header row
                    header_cols = st.columns([2, 1, 1, 2])
                    with header_cols[0]:
                        st.markdown("**Ticker**")
                    with header_cols[1]:
                        st.markdown("**Weight**")
                    with header_cols[2]:
                        st.markdown("**Allocation**")
                    with header_cols[3]:
                        st.markdown("**Actions**")
                    
                    st.markdown("---")
                    
                    # Initialize edit state
                    if "editing_ticker" not in st.session_state:
                        st.session_state.editing_ticker = None
                    
                    # Portfolio items with edit and delete buttons
                    for ticker, weight in portfolio_items:
                        row_cols = st.columns([2, 1, 1, 2])
                        with row_cols[0]:
                            st.markdown(f"**{ticker}**")
                        with row_cols[1]:
                            st.markdown(f"{weight:.1%}")
                        with row_cols[2]:
                            st.progress(weight, text=f"{weight:.1%}")
                        with row_cols[3]:
                            btn_cols = st.columns(2)
                            with btn_cols[0]:
                                if st.button("Edit", key=f"edit_{ticker}", type="secondary", use_container_width=True):
                                    st.session_state.editing_ticker = ticker
                                    st.rerun()
                            with btn_cols[1]:
                                if st.button("Delete", key=f"delete_{ticker}", type="secondary", use_container_width=True):
                                    try:
                                        PortfolioManager.remove_ticker(
                                            st.session_state.user["id"],
                                            ticker
                                        )
                                        st.session_state.portfolio = get_user_portfolio(
                                            st.session_state.user["id"]
                                        )
                                        st.success(f"Removed {ticker} from portfolio")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error removing {ticker}: {e}")
                    
                    # Edit weight modal
                    if st.session_state.editing_ticker:
                        st.markdown("---")
                        st.markdown(f"### Edit Weight for {st.session_state.editing_ticker}")
                        
                        current_weight = st.session_state.portfolio[st.session_state.editing_ticker]
                        
                        new_weight_pct = st.number_input(
                            "New Weight (%)",
                            min_value=0.1,
                            max_value=100.0,
                            value=current_weight * 100,
                            step=0.1,
                            format="%.1f",
                            key="weight_input"
                        )
                        
                        edit_cols = st.columns(3)
                        with edit_cols[0]:
                            if st.button("Save", type="primary", use_container_width=True):
                                try:
                                    new_weight = new_weight_pct / 100.0
                                    PortfolioManager.update_ticker_weight(
                                        st.session_state.user["id"],
                                        st.session_state.editing_ticker,
                                        new_weight
                                    )
                                    st.session_state.portfolio = get_user_portfolio(
                                        st.session_state.user["id"]
                                    )
                                    st.success(f"Updated {st.session_state.editing_ticker} weight to {new_weight:.1%}")
                                    st.session_state.editing_ticker = None
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating weight: {e}")
                        
                        with edit_cols[1]:
                            if st.button("Normalize All", type="secondary", use_container_width=True):
                                try:
                                    PortfolioManager.normalize_weights(st.session_state.user["id"])
                                    st.session_state.portfolio = get_user_portfolio(
                                        st.session_state.user["id"]
                                    )
                                    st.success("Portfolio weights normalized to 100%")
                                    st.session_state.editing_ticker = None
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error normalizing weights: {e}")
                        
                        with edit_cols[2]:
                            if st.button("Cancel", use_container_width=True):
                                st.session_state.editing_ticker = None
                                st.rerun()
                    
                    # Alternative: Also show as dataframe for better visualization
                    st.markdown("---")
                    st.markdown("#### Portfolio Overview")
                    portfolio_data = [
                        {"Ticker": ticker, "Weight": f"{weight:.1%}", "Allocation": weight}
                        for ticker, weight in portfolio_items
                    ]
                    st.dataframe(
                        portfolio_data,
                        column_config={
                            "Ticker": st.column_config.TextColumn("Ticker", width="medium"),
                            "Weight": st.column_config.TextColumn("Weight", width="small"),
                            "Allocation": st.column_config.ProgressColumn(
                                "Allocation",
                                min_value=0,
                                max_value=1,
                                format="%.1%%"
                            )
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                
                with col2:
                    # Portfolio summary
                    total_weight = sum(st.session_state.portfolio.values())
                    
                    if abs(total_weight - 1.0) < 0.01:
                        st.success("Portfolio weights are balanced (100%)")
                    else:
                        st.warning(f"Total weight: {total_weight:.1%} (should be 100%)")
                        if st.button("Normalize to 100%", type="primary", use_container_width=True, key="normalize_summary"):
                            try:
                                PortfolioManager.normalize_weights(st.session_state.user["id"])
                                st.session_state.portfolio = get_user_portfolio(
                                    st.session_state.user["id"]
                                )
                                st.success("Portfolio weights normalized!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error normalizing: {e}")
                    
                    # Tickers display
                    st.markdown("**Tracked Tickers:**")
                    tickers_html = " ".join([
                        f'<span class="ticker-badge">{ticker}</span>'
                        for ticker in st.session_state.portfolio.keys()
                    ])
                    st.markdown(tickers_html, unsafe_allow_html=True)
                
                # Recent runs
                st.markdown("---")
                st.markdown("### Recent Analysis Runs")
                
                recent_runs = get_recent_runs(st.session_state.user["id"])
                
                if recent_runs:
                    for run in recent_runs:
                        status_text = {
                            "completed": "Completed",
                            "running": "Running",
                            "failed": "Failed"
                        }.get(run["status"], "Unknown")
                        
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.text(f"{status_text} - Run #{run['id']}")
                        with col2:
                            if run["started_at"]:
                                st.text(run["started_at"].strftime("%Y-%m-%d %H:%M"))
                        with col3:
                            if run["execution_time"]:
                                st.text(f"{run['execution_time']}s")
                else:
                    st.info("No analysis runs yet. Reports run daily at 8am EST.")
                
            else:
                st.info("Go to **Add Stocks** tab to build your portfolio!")
        
        # Add Stocks Tab
        with tabs[1]:
            st.markdown("### Add Stocks to Portfolio")
            
            col1, col2 = st.columns(2)
            
            with col1:
                ticker = st.text_input(
                    "Stock Ticker",
                    placeholder="e.g., AAPL",
                    help="Enter the stock ticker symbol (e.g., AAPL for Apple)"
                ).upper().strip()
            
            with col2:
                weight = st.number_input(
                    "Portfolio Weight",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.1,
                    step=0.05,
                    format="%.2f",
                    help="Weight as decimal (0.1 = 10%)"
                )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Add to Portfolio", use_container_width=True):
                    if ticker:
                        try:
                            PortfolioManager.add_ticker(
                                st.session_state.user["id"],
                                ticker,
                                weight
                            )
                            st.session_state.portfolio = get_user_portfolio(
                                st.session_state.user["id"]
                            )
                            st.success(f"Added {ticker} with {weight:.1%} weight!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.warning("Please enter a ticker symbol.")
            
            with col2:
                if ticker and ticker in st.session_state.portfolio:
                    if st.button("Remove from Portfolio", use_container_width=True):
                        try:
                            PortfolioManager.remove_ticker(
                                st.session_state.user["id"],
                                ticker
                            )
                            st.session_state.portfolio = get_user_portfolio(
                                st.session_state.user["id"]
                            )
                            st.success(f"Removed {ticker}!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            
            # Current portfolio management
            if st.session_state.portfolio:
                st.markdown("---")
                st.markdown("### Current Portfolio")
                st.markdown("Manage your existing holdings:")
                
                # Display current stocks with delete buttons
                for ticker, weight in sorted(st.session_state.portfolio.items(), key=lambda x: x[1], reverse=True):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.markdown(f"**{ticker}** - {weight:.1%}")
                    with col2:
                        st.progress(weight, text=f"{weight:.1%}")
                    with col3:
                        if st.button("Delete", key=f"delete_add_{ticker}", type="secondary", use_container_width=True):
                            try:
                                PortfolioManager.remove_ticker(
                                    st.session_state.user["id"],
                                    ticker
                                )
                                st.session_state.portfolio = get_user_portfolio(
                                    st.session_state.user["id"]
                                )
                                st.success(f"Removed {ticker} from portfolio")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error removing {ticker}: {e}")
            
            # Quick add popular stocks
            st.markdown("---")
            st.markdown("### Quick Add Popular Stocks")
            
            popular_stocks = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", "V", "JNJ"]
            
            cols = st.columns(5)
            for i, stock in enumerate(popular_stocks):
                with cols[i % 5]:
                    if stock not in st.session_state.portfolio:
                        if st.button(f"+ {stock}", key=f"quick_{stock}", use_container_width=True):
                            try:
                                PortfolioManager.add_ticker(
                                    st.session_state.user["id"],
                                    stock,
                                    0.1
                                )
                                st.session_state.portfolio = get_user_portfolio(
                                    st.session_state.user["id"]
                                )
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                    else:
                        st.button(f"Added {stock}", key=f"quick_{stock}", disabled=True, use_container_width=True)
            
            # Bulk import
            st.markdown("---")
            st.markdown("### Bulk Import")
            
            bulk_input = st.text_area(
                "Enter tickers and weights (one per line)",
                placeholder="AAPL,0.3\nMSFT,0.3\nGOOGL,0.4",
                help="Format: TICKER,WEIGHT (e.g., AAPL,0.3)"
            )
            
            if st.button("Import Portfolio", use_container_width=True):
                if bulk_input:
                    success_count = 0
                    error_count = 0
                    
                    for line in bulk_input.strip().split("\n"):
                        try:
                            parts = line.strip().split(",")
                            if len(parts) == 2:
                                t = parts[0].strip().upper()
                                w = float(parts[1].strip())
                                PortfolioManager.add_ticker(
                                    st.session_state.user["id"],
                                    t,
                                    w
                                )
                                success_count += 1
                        except Exception:
                            error_count += 1
                    
                    st.session_state.portfolio = get_user_portfolio(
                        st.session_state.user["id"]
                    )
                    
                    if success_count > 0:
                        st.success(f"Imported {success_count} stocks!")
                    if error_count > 0:
                        st.warning(f"{error_count} lines had errors.")
                    
                    st.rerun()
        
        # Settings Tab
        with tabs[2]:
            st.markdown("### Settings")
            
            # Normalize weights
            st.markdown("#### Portfolio Weight Normalization")
            
            if st.session_state.portfolio:
                total = sum(st.session_state.portfolio.values())
                
                if abs(total - 1.0) > 0.01:
                    st.warning(f"Current total weight: {total:.1%}")
                    
                    if st.button("Normalize Weights to 100%", use_container_width=True):
                        try:
                            normalized = {
                                ticker: weight / total
                                for ticker, weight in st.session_state.portfolio.items()
                            }
                            PortfolioManager.update_portfolio(
                                st.session_state.user["id"],
                                normalized
                            )
                            st.session_state.portfolio = normalized
                            st.success("Weights normalized!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    st.success("Portfolio weights are already normalized.")
            
            # Clear portfolio
            st.markdown("---")
            st.markdown("#### Danger Zone")
            
            if st.button("Clear Entire Portfolio", type="secondary"):
                st.session_state.confirm_clear = True
            
            if st.session_state.get("confirm_clear"):
                st.warning("Are you sure? This will remove all stocks from your portfolio.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Yes, Clear All", type="primary"):
                        try:
                            with db_manager.get_session() as session:
                                session.query(Portfolio)\
                                    .filter(Portfolio.user_id == st.session_state.user["id"])\
                                    .delete()
                                session.commit()
                            st.session_state.portfolio = {}
                            st.session_state.confirm_clear = False
                            st.success("Portfolio cleared!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                with col2:
                    if st.button("Cancel"):
                        st.session_state.confirm_clear = False
                        st.rerun()
            
            # Manual run trigger
            st.markdown("---")
            st.markdown("#### Manual Analysis Run")
            
            st.info("Sentiment analysis runs automatically every weekday at 8am EST.")
            
            if st.button("Run Analysis Now", disabled=not st.session_state.portfolio):
                st.warning("Manual runs are currently disabled in the web interface. Use the CLI: `python main.py --user-id " + str(st.session_state.user["id"]) + "`")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #64748b; font-size: 0.8rem;">
            Portfolio Sentiment Intelligence Agent • Built with Streamlit<br>
            Reports are sent daily at 8am EST on weekdays
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

