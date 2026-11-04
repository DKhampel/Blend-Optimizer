import streamlit as st
import pulp as pl
from pulp import LpStatus
import pandas as pd

# 🎛️ Configure the webpage layout to look like a pro application dashboard
st.set_page_config(page_title="LP Blend Optimizer", page_icon="🎛️", layout="wide")
st.title("🎛️ Interactive Optimization Blend Dashboard")
st.markdown("Adjust targets, engineering specs, and penalty variables, then click 'Create Optimized Blend' to calculate.")

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
    st.session_state.lots_data = pd.DataFrame([
        {"Lot": lot, "Cost": Cost[lot], "Capacity": bounds[lot]}
        for lot in bounds
    ])

if "specs_data" not in st.session_state:
    st.session_state.specs_data = pd.DataFrame([
        {
            "Attribute": attr,
            "Min": limits[0],
            "Max": limits[1],
            "Target": limits[2],
        }
        for attr, limits in default_specs.items()
    ])

if "values_data" not in st.session_state:
    st.session_state.values_data = pd.DataFrame([
        {"Attribute": attr, "Lot": lot, "Value": value}
        for attr, lot_values in Attributes.items()
        for lot, value in lot_values.items()
    ])
# --- ⚙️ LINEAR PROGRAMMING SOLVER CORE ---
def solve_for_lambda(lmbda, total_units_required, lots_df, specs_df, values_df):
    lots = lots_df.set_index("Lot").to_dict("index")
    specs = specs_df.set_index("Attribute").to_dict("index")
    values = {
        (row["Attribute"], row["Lot"]): row["Value"]
        for _, row in values_df.iterrows()
    }

    lot_names = list(lots)
    attr_names = list(specs)

    x = {
        lot: pl.LpVariable(
            f"lot_{index}",
            lowBound=0,
            upBound=float(lots[lot]["Capacity"]),
        )
        for index, lot in enumerate(lot_names)
    }

    prob = pl.LpProblem("Blend_Quality_Cost", pl.LpMinimize)
    total_units = pl.lpSum(x.values())
    prob += total_units == total_units_required

    deviation_vars = {}
    for index, attr in enumerate(attr_names):
        pos = pl.LpVariable(f"attr_{index}_pos", lowBound=0)
        neg = pl.LpVariable(f"attr_{index}_neg", lowBound=0)
        deviation_vars[attr] = (pos, neg)

        spec = specs[attr]
        total_attr = pl.lpSum(
            values[(attr, lot)] * x[lot] for lot in lot_names
        )

        prob += total_attr >= spec["Min"] * total_units
        prob += total_attr <= spec["Max"] * total_units
        prob += total_attr - spec["Target"] * total_units == pos - neg

    total_cost = pl.lpSum(
        lots[lot]["Cost"] * x[lot] for lot in lot_names
    )
    total_deviation = pl.lpSum(
        pos + neg for pos, neg in deviation_vars.values()
    )
    prob += total_cost + lmbda * total_deviation

    prob.solve(pl.PULP_CBC_CMD(msg=False))
    status = LpStatus[prob.status]

    if status != "Optimal":
        return {"status": status}

    allocations = {lot: x[lot].value() for lot in lot_names}
    total_units_value = sum(allocations.values())

    results = {
        "status": status,
        "cost": sum(
            lots[lot]["Cost"] * allocations[lot] for lot in lot_names
        ),
        "deviation": sum(
            pos.value() + neg.value()
            for pos, neg in deviation_vars.values()
        ),
        "allocations": allocations,
    }

    for attr in attr_names:
        results[attr] = (
            sum(
                values[(attr, lot)] * allocations[lot]
                for lot in lot_names
            ) / total_units_value
            if total_units_value
            else None
        )

    return results

# --- 🛠️ INTERACTIVE SIDEBAR CONTROLS ---
# Using explicit sidebar context cleanly fixes rendering drops
with st.sidebar:
    st.header("🎯 Target Parameters")
    total_units_required = st.number_input(
        "Total Units Required", min_value=0, value=100000, step=1000
    )
    lmbda = st.slider(
        "Select Penalty Weight (λ)", min_value=0, max_value=5000, value=100, step=10
    )
    st.divider()

    submit_button = st.button(
        label="⚡ Create Optimized Blend",
        use_container_width=True,
        type="primary",
    )
st.subheader("Resource lots")
lots_df = st.data_editor(
    st.session_state.lots_data,
    num_rows="dynamic",
    key="lots_editor",
    column_config={
        "Lot": st.column_config.TextColumn("Lot name", required=True),
        "Cost": st.column_config.NumberColumn("Cost", min_value=0, required=True),
        "Capacity": st.column_config.NumberColumn("Capacity", min_value=0, required=True),
    },
    use_container_width=True,
)

st.subheader("Attribute specifications")
specs_df = st.data_editor(
    st.session_state.specs_data,
    num_rows="dynamic",
    key="specs_editor",
    column_config={
        "Attribute": st.column_config.TextColumn("Attribute name", required=True),
        "Min": st.column_config.NumberColumn("Minimum", required=True),
        "Max": st.column_config.NumberColumn("Maximum", required=True),
        "Target": st.column_config.NumberColumn("Target", required=True),
    },
    use_container_width=True,
)

st.subheader("Attribute values for each lot")
values_df = st.data_editor(
    st.session_state.values_data,
    num_rows="dynamic",
    key="values_editor",
    column_config={
        "Attribute": st.column_config.TextColumn("Attribute name", required=True),
        "Lot": st.column_config.TextColumn("Lot name", required=True),
        "Value": st.column_config.NumberColumn("Value", required=True),
    },
    use_container_width=True,
)
# --- 📊 VISUAL DASHBOARD GENERATION ---
if submit_button:
    result = solve_for_lambda(
        lmbda,
        total_units_required,
        lots_df,
        specs_df,
        values_df,
    )

    if result["status"] != "Optimal":
        st.error(f"Solver Status: {result['status']}")
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.success(f"Solver Status: {result['status']}")
        with c2:
            st.metric("Calculated Total Cost", f"${result['cost']:,.2f}")
        with c3:
            st.metric("Total Quality Deviation", f"{result['deviation']:.2f}")

        st.divider()

        left_panel, right_panel = st.columns(2)

        with left_panel:
            st.subheader("📈 Realized Quality Attribute Metrics")
            infeasible_attrs = []

            for _, spec in specs_df.iterrows():
                attr = spec["Attribute"]
                min_val = spec["Min"]
                max_val = spec["Max"]
                target = spec["Target"]
                avg_val = result[attr]

                with st.container(border=True):
                    st.markdown(
                        f"**{attr}** (Target: {target} | "
                        f"Allowed: [{min_val} - {max_val}])"
                    )
                    if avg_val < min_val or avg_val > max_val:
                        st.markdown(
                            f"Realized Blend: :red[{avg_val:.2f} ⚠️ Out of Spec!]"
                        )
                        infeasible_attrs.append(attr)
                    else:
                        st.markdown(
                            f"Realized Blend: :green[{avg_val:.2f} ✅ Within Range]"
                        )

            if infeasible_attrs:
                st.warning(
                    "💡 System Alert: Parameters are physically **infeasible** "
                    f"for: {', '.join(infeasible_attrs)}."
                )
            else:
                st.info("✅ Ideal Blend Achieved: All operational specs satisfied.")

        with right_panel:
            st.subheader("📦 Resource Lot Allocation Matrix")
            capacities = lots_df.set_index("Lot")["Capacity"]

            df_alloc = pd.DataFrame({
                "Lot Number": list(result["allocations"].keys()),
                "Allocated Volume": list(result["allocations"].values()),
                "Capacity Ceiling": [
                    capacities[lot] for lot in result["allocations"]
                ],
            })
            st.dataframe(df_alloc, hide_index=True, use_container_width=True)
            st.bar_chart(data=df_alloc, x="Lot Number", y="Allocated Volume")
else:
    st.info(
        "👈 Set your engineering constraints in the sidebar and click "
        "**'Create Optimized Blend'** to calculate results."
    )

