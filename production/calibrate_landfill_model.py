import numpy as np
import pandas as pd
from scipy.optimize import least_squares
DEFAULT_METHANE_PERCENT = 50

def calibrate_model(df_prod, ch4_default = False, use_relative = False, use_annual = True, use_MAD = False):
    data_collected_year = 2022
    if use_annual:
        cols = ["Year Landfill Opened", "Landfill Closure Year", "Annual Waste Acceptance Rate (tons per year)", "LFG Generated (mmscfd)"]
        df_prod = df_prod.dropna(subset=cols)
    else:
        cols = ["Year Landfill Opened", "Landfill Closure Year", "Waste in Place (tons)", "LFG Generated (mmscfd)"]
        df_prod = df_prod.dropna(subset=cols)
        t_d = np.minimum(data_collected_year, df_prod["Landfill Closure Year"]) - df_prod["Year Landfill Opened"]
        df_prod["Annual Waste Acceptance Rate (tons per year)"] = df_prod["Waste in Place (tons)"] / t_d

    if ch4_default:
        df_prod["Methane Percent"] = 50.0
    else:
        df_prod["Methane Percent"] = df_prod["Methane Percent"].fillna(50.0)
    total_waste = df_prod["Annual Waste Acceptance Rate (tons per year)"]
    year_open = df_prod["Year Landfill Opened"]
    year_close = df_prod['Landfill Closure Year']
    LFG_obs = df_prod["LFG Generated (mmscfd)"]
    ch4_percent = df_prod["Methane Percent"]
    x0 = [0.05, 3204]                 # initial guess (your current defaults)
    bounds = ([1e-4, 1.0], [1.0, 1e6]) # reasonable bounds; tune for your domain
    if use_relative:
        res = least_squares(
            residuals_rel, x0=x0, bounds=bounds,
            args=(total_waste, year_open, year_close, ch4_percent, LFG_obs)
        )
    else:
        res = least_squares(
            residuals, x0=x0, bounds=bounds,
            args=(total_waste, year_open, year_close, ch4_percent, LFG_obs)
        )
    
    if use_MAD:
        k0, L00 = res.x  # from your current fit
        x0 = res.x
        pred = np.array([
            predict_LFG_mmscfd(w, yo, yc, ch4, k0, L00)
                for w, yo, yc, ch4 in zip(total_waste, year_open, year_close, ch4_percent)
            ])
        if use_relative:
            rel = (pred - np.asarray(LFG_obs)) / (np.asarray(LFG_obs) + 1e-9)  # signed relative residual
            abs_rel = np.abs(rel)
            med = np.median(rel)
            mad = np.median(np.abs(rel - med)) + 1e-12
            robust_z = 0.6745 * (rel - med) / mad     # robust z-score

            mask_inlier = np.abs(robust_z) <= 3.5     # 3.5 is a common cutoff
            res = least_squares(
                    residuals_rel, x0=x0, bounds=bounds,
                    args=(total_waste[mask_inlier], year_open[mask_inlier], year_close[mask_inlier], ch4_percent[mask_inlier], LFG_obs[mask_inlier])
                )
            print("Removed Outliers:")
            print(LFG_obs[~mask_inlier])
            print("Removed outliers:", np.sum(~mask_inlier))
            k_fit, L0_fit = res.x
        else:
            rel = (pred - np.asarray(LFG_obs))  # signed relative residual
            abs_rel = np.abs(rel)
            med = np.median(rel)
            mad = np.median(np.abs(rel - med)) + 1e-12
            robust_z = 0.6745 * (rel - med) / mad     # robust z-score

            mask_inlier = np.abs(robust_z) <= 3.5     # 3.5 is a common cutoff
            res = least_squares(
                    residuals, x0=x0, bounds=bounds,
                    args=(total_waste[mask_inlier], year_open[mask_inlier], year_close[mask_inlier], ch4_percent[mask_inlier], LFG_obs[mask_inlier])
                )
            print("Removed Outliers:")
            print(LFG_obs[~mask_inlier])
            print("Removed outliers:", np.sum(~mask_inlier))
            k_fit, L0_fit = res.x
    else:
        k_fit, L0_fit = res.x
    print("k =", k_fit)
    print("L0 =", L0_fit)
    print("RMSE (mmscfd) =", np.sqrt(np.mean(res.fun**2)))


def predict_LFG_mmscfd(total_waste, year_open, year_close, ch4_percent, k, L0,
                       curr_year=2022, data_collected_year=2022):
    R = total_waste

    c = curr_year - min(curr_year, year_close)
    t = curr_year - year_open

    Qt = (1/(ch4_percent * 0.01)) * L0 * R * (np.exp(-k*c) - np.exp(-k*t))  # ft^3/yr
    return Qt / (365 * 1e6)  # mmscfd

def residuals(params, total_waste, year_open, year_close, ch4_percent, LFG_obs):
    k, L0 = params
    pred = np.array([
        predict_LFG_mmscfd(w, yo, yc, ch4, k, L0)
        for w, yo, yc, ch4 in zip(total_waste, year_open, year_close, ch4_percent)
    ])
    obs = np.asarray(LFG_obs)
    eps = 1e-9
    return (pred - obs) # / (obs + eps)

def residuals_rel(params, total_waste, year_open, year_close, ch4_percent, LFG_obs):
    k, L0 = params
    pred = np.array([
        predict_LFG_mmscfd(w, yo, yc, ch4, k, L0)
        for w, yo, yc, ch4 in zip(total_waste, year_open, year_close, ch4_percent)
    ])
    obs = np.asarray(LFG_obs)
    eps = 1e-9
    return (pred - obs) / (obs + eps)

