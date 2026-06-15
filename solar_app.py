import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.title("Solar Cell Parameter Extraction Tool")

# Inputs
Area = st.number_input(
    "Area (cm²)",
    min_value=0.0001,
    value=0.0078,
    step=0.0001,
    format="%.4f",
    key="area_input_final"
)
Astar = st.number_input("A*", value=120.0)
T = st.number_input("Temperature (K)", value=300.0)

uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx","xls"]
)

# =====================================
# CHEUNG PART 1
# =====================================

if st.button("Run Cheung Part 1"):

    if uploaded_file is None:
        st.error("Please upload an Excel file")

    else:

        data = pd.read_excel(uploaded_file)

        V = data.iloc[:,0].values
        I = data.iloc[:,1].values

        # Forward bias region
        idx = V > 0

        Vf = V[idx]
        If = I[idx]

        # Remove non-positive currents
        idx2 = If > 0

        Vf = Vf[idx2]
        If = If[idx2]

        # Downsample
        Vf = Vf[::10]
        If = If[::10]

        # Cheung Part 1
        lnI = np.log(If)

        dV = np.diff(Vf)
        dlnI = np.diff(lnI)

        Y = dV / dlnI

        I_mid = If[:-1]

        # Linear region
        idx_fit = I_mid < 0.022

        I_fit = I_mid[idx_fit]
        Y_fit_data = Y[idx_fit]

        # Linear fit
        p = np.polyfit(I_fit,Y_fit_data,1)

        Rs = p[0]
        Intercept = p[1]

        q = 1.602e-19
        k = 1.381e-23

        n = (q/(k*T))*Intercept

        # Fitted line
        Y_fit = np.polyval(p,I_fit)

        st.success("Cheung Part 1 Completed")

        st.write(f"### Rs = {Rs:.4f} Ω")
        st.write(f"### n = {n:.4f}")
        st.write(f"### Intercept = {Intercept:.4f}")

        # Plot
        fig, ax = plt.subplots(figsize=(8,5))

        ax.plot(
            I_mid,
            Y,
            '.',
            markersize=8,
            label='Experimental Data'
        )

        ax.plot(
            I_fit,
            Y_fit,
            'r',
            linewidth=2,
            label='Linear Fit'
        )

        ax.set_xlabel("Current (A)")
        ax.set_ylabel("dV / dln(I)")
        ax.set_title("Cheung Method Part 1")

        ax.grid(True)
        ax.legend()

        st.pyplot(fig)

# =====================================
# CHEUNG PART 2
# =====================================

if st.button("Run Cheung Part 2"):

    if uploaded_file is None:
        st.error("Please upload an Excel file")

    else:

        data = pd.read_excel(uploaded_file)

        V = data.iloc[:,0].values
        I = data.iloc[:,1].values

        # Forward bias region
        idx = V > 0

        Vf = V[idx]
        If = I[idx]

        # Remove non-positive currents
        idx2 = If > 0

        Vf = Vf[idx2]
        If = If[idx2]

        # Downsample
        Vf = Vf[::10]
        If = If[::10]

        q = 1.602e-19
        k = 1.381e-23

        # ----------------------
        # Calculate n from Part 1
        # ----------------------

        lnI = np.log(If)

        dV = np.diff(Vf)
        dlnI = np.diff(lnI)

        Y = dV / dlnI

        I_mid = If[:-1]

        idx_fit = I_mid < 0.022

        I_fit = I_mid[idx_fit]
        Y_fit_data = Y[idx_fit]

        p = np.polyfit(I_fit,Y_fit_data,1)

        Rs1 = p[0]
        Intercept = p[1]

        n = (q/(k*T))*Intercept

        # ----------------------
        # Cheung Part 2
        # ----------------------

        H = Vf - n*(k*T/q)*np.log(
            If/(Area*Astar*(T**2))
        )

        idx_fit2 = If < 0.022

        I_fit2 = If[idx_fit2]
        H_fit_data = H[idx_fit2]

        p2 = np.polyfit(
            I_fit2,
            H_fit_data,
            1
        )

        Rs2 = p2[0]
        Intercept2 = p2[1]

        Phi_B = Intercept2 / n

        # Reverse Saturation Current
        VT = 0.02585   # kT/q at 300 K

        Is = Area * Astar * (T**2) * np.exp(-Phi_B / VT)

        H_fit = np.polyval(
            p2,
            I_fit2
        )

        st.success("Cheung Part 2 Completed")

        st.write(f"### Rs (Part 2) = {Rs2:.4f} Ω")
        st.write(f"### Barrier Height = {Phi_B:.4f} eV")
        st.write(f"### Intercept = {Intercept2:.4f}")
        st.write(f"### Reverse saturation current Is = {Is:.4e} A")
        # =====================================================
        # VOLTAGE CONTROLLED IDEALITY FACTOR
        # =====================================================

        # Use complete forward bias region
        mask_vcif = If > 0

        Vf_fit = Vf[mask_vcif]
        If_fit = If[mask_vcif]

        # Avoid log(1) and negative values
        ratio = If_fit / Is
        valid = ratio > 1.05

        Vf_fit = Vf_fit[valid]
        If_fit = If_fit[valid]

        # Voltage controlled ideality factor
        nV = Vf_fit / ((k*T/q) * np.log(If_fit/Is))

       # Remove invalid values
        valid_nv = np.isfinite(nV) & (nV > 0)

        nV = nV[valid_nv]
        Vf_fit = Vf_fit[valid_nv]
        If_fit = If_fit[valid_nv]

        st.subheader("Voltage Controlled Ideality Factor")

        st.write(f"Average n(V) = {np.mean(nV):.4f}")

        fig_nv, ax_nv = plt.subplots(figsize=(8,5))
        ax_nv.plot(Vf_fit, nV, linewidth=2)
        ax_nv.set_xlabel("Voltage (V)")
        ax_nv.set_ylabel("n(V)")
        ax_nv.set_title("Voltage Controlled Ideality Factor")
        ax_nv.grid(True)

        st.pyplot(fig_nv)

# =====================================================
# EFFECTIVE BARRIER HEIGHT
# =====================================================

        Phi_eff = Phi_B + (1 - 1/nV) * (Vf_fit - If_fit*Rs1)

        valid_phi = np.isfinite(Phi_eff)

        Phi_eff = Phi_eff[valid_phi]
        Vf_phi = Vf_fit[valid_phi]

        st.subheader("Effective Barrier Height")

        st.write(
        f"Average Effective Barrier Height = "
        f"{np.mean(Phi_eff):.4f} eV")

        fig_phi, ax_phi = plt.subplots(figsize=(8,5))

        ax_phi.plot(Vf_phi, Phi_eff, linewidth=2)

        ax_phi.set_xlabel("Voltage (V)")
        ax_phi.set_ylabel("Effective Barrier Height (eV)")
        ax_phi.set_title("Effective Barrier Height")
        ax_phi.grid(True)

        st.pyplot(fig_phi)

        # Plot

        fig, ax = plt.subplots(figsize=(8,5))

        ax.plot(
            If,
            H,
            '.',
            markersize=8,
            label='Experimental Data'
        )

        ax.plot(
            I_fit2,
            H_fit,
            'r',
            linewidth=2,
            label='Linear Fit'
        )

        ax.set_xlabel("Current (A)")
        ax.set_ylabel("H(I)")
        ax.set_title("Cheung Method Part 2")

        ax.grid(True)
        ax.legend()

        st.pyplot(fig)
