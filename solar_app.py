import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import streamlit as st

st.set_page_config(
    page_title="Solar Cell Analyzer",
    page_icon="☀️",
    layout="wide"
)

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
st.subheader("Nss Parameters")

eps_i = st.number_input(
    "Dielectric Constant of SiO₂",
    value=3.9
)

delta_nm = st.number_input(
    "Oxide Thickness (nm)",
    value=2.0,
    step=0.0000001,
    format="%.6f"
)

Wd_nm = st.number_input(
    "Depletion Width (nm)",
    value=20.0,
    step=0.0000001,
    format="%.6f"
)

eps_s = st.number_input(
    "Dielectric Constant of Silicon",
    value=11.9
)

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
        
        V_all = V.copy()
        I_all = I.copy()

        st.session_state["V_all"] = V_all
        st.session_state["I_all"] = I_all

        idx = V > 0

        Vf = V[idx]
        If = I[idx]

        # Remove non-positive currents
        idx2 = If > 0

        Vf = Vf[idx2]
        If = If[idx2]

        # Downsample ONLY for Cheung fitting
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

        V_all = V.copy()
        I_all = I.copy()

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
        # Save values for later use

        st.session_state["V_all"] = V_all
        st.session_state["I_all"] = I_all
        st.session_state["Vf"] = Vf
        st.session_state["If"] = If
        st.session_state["Rs"] = Rs1
        st.session_state["Phi_B"] = Phi_B
        st.session_state["Is"] = Is
        st.session_state["n"] = n
        st.session_state["Area"] = Area
        st.session_state["T"] = T

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
        # =====================================================
# VOLTAGE CONTROLLED IDEALITY FACTOR
# =====================================================

if st.button("Voltage Controlled Ideality Factor"):

    if "Vf" not in st.session_state:
        st.error("Run Cheung Part 2 first")
    else:

        q = 1.602e-19
        k = 1.381e-23

        V_all = st.session_state["V_all"]
        I_all = st.session_state["I_all"]
        Is = st.session_state["Is"]
        T = st.session_state["T"]

       # Use all forward-bias points
        Vf_plot = V_all
        If_plot = I_all

        nV = Vf_plot / (
            (k*T/q) *
            np.log(If_plot/Is)
        )

        valid2 = np.isfinite(nV)

        nV = nV[valid2]
        Vf_plot = Vf_plot[valid2]
        If_plot = If_plot[valid2]

        st.subheader("Voltage Controlled Ideality Factor")

        st.write(f"Average n(V) = {np.mean(nV):.4f}")
        st.write(f"Minimum n(V) = {np.min(nV):.4f}")
        st.write(f"Maximum n(V) = {np.max(nV):.4f}")

        fig, ax = plt.subplots(figsize=(8,5))

        ax.plot(
            Vf_plot,
            nV,
            linewidth=2
        )

        ax.set_xlabel("Voltage (V)")
        ax.set_ylabel("n(V)")
        ax.set_title("Voltage Controlled Ideality Factor")
        ax.grid(True)

        st.pyplot(fig)

        st.session_state["nV"] = nV
        st.session_state["Vf_plot"] = Vf_plot

        st.write("Total Voltage Points =", len(V_all))
        st.write("Points after VCIF =", len(nV))
        st.write("Points after filtering =", len(Vf_plot))


        # =====================================================
# EFFECTIVE BARRIER HEIGHT
# =====================================================

if st.button("Effective Barrier Height"):

    if "nV" not in st.session_state:
        st.error("Run Voltage Controlled Ideality Factor first")
    else:

        Phi_B = st.session_state["Phi_B"]
        Rs = st.session_state["Rs"]

        Vf_plot = st.session_state["Vf_plot"]
        nV = st.session_state["nV"]

        Phi_eff = Phi_B + (1 - 1/nV) * Vf_plot

        valid = np.isfinite(Phi_eff)

        Phi_eff = Phi_eff[valid]
        Vf_phi = Vf_plot[valid]

        st.subheader("Effective Barrier Height")

        st.write(
            f"Average Effective Barrier Height = "
            f"{np.mean(Phi_eff):.4f} eV"
        )

        fig, ax = plt.subplots(figsize=(8,5))

        ax.plot(
            Vf_phi,
            Phi_eff,
            linewidth=2
        )

        ax.set_xlabel("Voltage (V)")
        ax.set_ylabel("Φe (eV)")
        ax.set_title("Effective Barrier Height")
        ax.grid(True)

        st.pyplot(fig)

        st.session_state["Phi_eff"] = Phi_eff
        st.session_state["Vf_phi"] = Vf_phi

        # =====================================================
# INTERFACIAL STATE DENSITY (Nss)
# =====================================================

if st.button("Interfacial State Density (Nss)"):

    if "nV" not in st.session_state:
        st.error("Run Voltage Controlled Ideality Factor first")

    elif "Phi_eff" not in st.session_state:
        st.error("Run Effective Barrier Height first")

    else:

        q = 1.602e-19
        eps0 = 8.854e-14   # F/cm

        nV = st.session_state["nV"]
        Phi_eff = st.session_state["Phi_eff"]
        V_all = st.session_state["V_all"]
        I_all = st.session_state["I_all"]

        # Convert nm → cm
        delta_cm = delta_nm * 1e-7
        Wd_cm = Wd_nm * 1e-7

        # -----------------------------
        # Capacitance terms
        # -----------------------------
        Cox = 5.46e-10      # F
        Area = 0.0078       # cm²
        Ci = Cox / Area
        Cd = eps_s * eps0 / Wd_cm

        # Retrieve complete voltage data
        V_all = st.session_state["V_all"]

        # Retrieve forward-bias results
        Phi_B = st.session_state["Phi_B"]
        Vf_phi = st.session_state["Vf_phi"]
        nV = st.session_state["nV"]
        

        Ess_minus_Ev = Phi_eff - Vf_phi

        # Nss
        # ------------------------------------
        Nss = ((Ci - Cd) * (nV - 1)) / q
        # Remove invalid values
        valid = np.isfinite(Nss) & np.isfinite(Ess_minus_Ev)
        Nss = Nss[valid]
        Ess_minus_Ev = Ess_minus_Ev[valid]
        Nss_ln = np.log(Nss)

        st.subheader("Interfacial State Density")

        st.write(f"Average ln(Nss) = {np.mean(Nss_ln):.4f}")


        fig_nss, ax_nss = plt.subplots(figsize=(8,5))

        ax_nss.plot(
        Ess_minus_Ev,
        Nss,
        linewidth=2
        )
        ax_nss.set_yscale('log')
        ax_nss.set_xlabel("Ess - Ev (eV)")
        ax_nss.set_ylabel("Nss (cm$^{-2}$ eV$^{-1}$)")
        ax_nss.set_title("Interfacial State Density")

        ax_nss.grid(True,which="both")

        st.pyplot(fig_nss)

        st.write("Maximum Phi_eff =", np.max(Phi_eff))
        st.write("Maximum Voltage =", np.max(Vf_phi))
        st.write("Calculated Ci =",Ci)

        st.write("Length of Phi_eff =", len(Phi_eff))
        st.write("Length of Ess-Ev =", len(Ess_minus_Ev))
        st.write("Length of Nss =", len(Nss))