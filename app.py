import streamlit as st
import pulp as pl
from pulp import LpStatus
import pandas as pd
# 🆕 Import the login form tool
from st_login_form import login_form

# 🎛️ Configure the webpage layout (must stay at the very top)
st.set_page_config(page_title="LP Blend Optimizer", page_icon="🎛️", layout="wide")

# 🆕 Render the Login / Create Account interface
client = login_form()

# 🔒 Guard check: Only run application code if the user passes authentication
if st.session_state["authenticated"]:
    
    # Provide a simple logout button in the sidebar panel
    if st.sidebar.button("Logout"):
        st.session_state["authenticated"] = False
        st.session_state["username"] = None
        st.rerun()

    st.title("🎛️ Interactive Optimization Blend Dashboard")
    st.markdown(f"Welcome **{st.session_state['username']}**! Adjust targets, engineering specs, and penalty variables, then click 'Create Optimized Blend' to calculate.")

    # --- STATIC DATASETS (From your original engineering matrix) ---
    Cost = {"x1": 1, "x2": 1.1, "x3": 1.2,"x4":1,"x5":1,"x6":1,"x7":1, "x8":1, "x9":1, "x10":1, "x11":1, "x12":1, "x13":1, "x14":1}
    bounds = {"x1": 15229, "x2": 17900, "x3": 17471,"x4":4154,"x5":37023,"x6":5600, "x7":10100, "x8":10100, "x9":10000, "x10":3660, "x11":6000, "x12":2500,"x13":1895,"x14":100000}
    Attributes = {
        "Attribute 1": {"x1": 68, "x2": 109, "x3": 95,"x4":118,"x5":97,"x6":54,"x7":101,"x8":37,"x9":54,"x10":121,"x11":117,"x12":118,"x13":97,"x14":0 },
        "Attribute 2": {"x1": 31, "x2": 152, "x3": 113,"x4":156,"x5":105,"x6":2,"x7":123,"x8":7,"x9":2,"x10":116,"x11":168,"x12":166,"x13":103,"x14":0},
        "Attribute 3": {"x1": 123, "x2": 97, "x3": 220,"x4":168,"x5":115,"x6":102,"x7":121,"x8":65.7,"x9":102,"x10":115,"x11":159,"x12":102,"x13":165,"x14":0},
        "Attribute 4": {"x1": 12.43, "x2": 9.1, "x3": 15.7,"x4":17.23,"x5":8.05,"x6":11.5,"x7":14.3,"x8":5.9,"x9":11.6,"x10":7.5,"x11":15.1,"x12":10.1,"x13":9.97,"x14":0},
        "Attribute 5": {"x1": 140, "x2": 93, "x3": 97.3,"x4":100,"x5":77.5,"x6":115,"x7":156,"x8":121,"x9":115,"x10":101,"x11":92,"x12":101,"x13":94,"x14":0}
    }
    default_specs = {
        "Attribute 1": (50, 150, 100),
        "Attribute 2": (100, 120, 110),
        "Attribute 3": (0, 1000, 75),
        "Attribute 4": (0, 5, 10),
        "Attribute 5": (98, 100, 98),
    }

    if "lots_data" not in st.session_state:
        st.session_state.lots_data = pd.DataFrame([])

    # (Ensure the rest of your optimization code layout remains indented right here)

else:
    # 🆕 Content displayed underneath the login box for unlogged users
    st.info("Please log in or create an account using the panel above to access the optimization dashboard tools.")
