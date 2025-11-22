import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# relative Pfade
git_dir = os.path.dirname(os.getcwd()) # Use this if using the main.ipynb file
#git_dir = os.getcwd() # Use this if using utils.py directly
data_dir = os.path.join(git_dir, 'data')
docs_dir = os.path.join(git_dir, 'docs')
machine_positions_path = os.path.join(data_dir, "machine_positions.txt")
transport_demand_path = os.path.join(data_dir, "transport_demand.txt")
val_res_path = os.path.join(data_dir, "validation_results.csv")
output_path_val_res = os.path.join(docs_dir, "validation_results.png")
output_path_best_val_res = os.path.join(docs_dir, "best_validation_results.png")

def read_txt_files():
  machine_positions = pd.read_csv(machine_positions_path, sep=r";", names =["machine_id", "x", "y"], header=0)
  transport_demand = pd.read_csv(transport_demand_path, sep=";")
  return machine_positions, transport_demand

def save_schedule(schedule, filename):
  schedule.to_csv(os.path.join(data_dir, filename), index=False)

def read_validation_results(filename):
  val_results = pd.read_csv(filename)
  car1_results = val_results[val_results["file"].str.contains("schedule_1_", na=False)].copy()
  car5_results = val_results[val_results["file"].str.contains("schedule_5_", na=False)].copy()
  car10_results = val_results[val_results["file"].str.contains("schedule_10_", na=False)].copy()

  car1_results["k"] = car1_results["file"].str.extract(r'k(\d+)').astype(int)
  car5_results["k"] = car5_results["file"].str.extract(r'k(\d+)').astype(int)
  car10_results["k"] = car10_results["file"].str.extract(r'k(\d+)').astype(int)

  car1_results["method"] = car1_results["file"].str.extract(r'schedule_\d+_(.+?)(?:_k|\.txt)')
  car5_results["method"] = car5_results["file"].str.extract(r'schedule_\d+_(.+?)(?:_k|\.txt)')
  car10_results["method"] = car10_results["file"].str.extract(r'schedule_\d+_(.+?)(?:_k|\.txt)')

  car1_results.drop(columns=["file"], inplace=True)
  car5_results.drop(columns=["file"], inplace=True)
  car10_results.drop(columns=["file"], inplace=True)

  car1_results = car1_results[["method", "k", "emptyRuns", "score"]].sort_values(by=["method", "k"])
  car5_results = car5_results[["method", "k", "emptyRuns", "score"]].sort_values(by=["method", "k"])
  car10_results = car10_results[["method", "k", "emptyRuns", "score"]].sort_values(by=["method", "k"])

  return car1_results, car5_results, car10_results

def plot_validation_results(show=False, save=False):
  car1_results, car5_results, car10_results = read_validation_results(val_res_path)
  fig, axs = plt.subplots(3, 1, figsize=(10, 14))

  # --- Plot for Car 1 ---
  labels = car1_results["method"] + "_k" + car1_results["k"].astype(str)
  scores = car1_results["score"]
  empty_runs = car1_results["emptyRuns"]
  x_positions = np.arange(len(labels))
  width = 0.4

  ## scores plot
  axs[0].bar(x_positions - width/2, scores, color='skyblue', width=width)
  for i, score in zip(x_positions, scores):
    axs[0].text(x=i-width/2, y=scores.min()-1000, s=f"{score:.2f}", ha='center', va='bottom', rotation=90, fontsize=10, fontweight='bold')

  ## empty runs plot
  axs_empty_runs = axs[0].twinx()
  axs_empty_runs.bar(x_positions + width/2, empty_runs, color='lightcoral', width=width)
  for i, empty_run in zip(x_positions, empty_runs):
    axs_empty_runs.text(x=i+width/2, y=empty_runs.min()-40, s=f"{empty_run}", ha='center', va='bottom', rotation=90, fontsize=10, fontweight='bold')

  ## plot settings
  axs_empty_runs.set_ylabel("Empty Runs", color='lightcoral', fontweight='bold')
  axs[0].set_title("Validation Results for 1 Car", fontweight='bold')
  axs[0].set_ylabel("Score", color='skyblue', fontweight='bold')
  axs[0].set_ylim(scores.min() * 0.9, scores.max() * 1.02)
  axs[0].set_xticks(x_positions)
  axs[0].set_xticklabels(labels, ha='center')

  # --- Plot for Car 5 ---
  labels = car5_results["method"] + "_k" + car5_results["k"].astype(str)
  scores = car5_results["score"]
  empty_runs = car5_results["emptyRuns"]
  x_positions = np.arange(len(labels))

  ## scores plot
  axs[1].bar(x_positions - width/2, scores, color='skyblue', width=width)
  for i, score in zip(x_positions, scores):
    axs[1].text(x=i-width/2, y=scores.min()-200, s=f"{score:.2f}", ha='center', va='bottom', rotation=90, fontsize=10, fontweight='bold')

  ## empty runs plot
  axs_empty_runs = axs[1].twinx()
  axs_empty_runs.bar(x_positions + width/2, empty_runs, color='lightcoral', width=width)
  for i, empty_run in zip(x_positions, empty_runs):
    axs_empty_runs.text(x=i+width/2, y=empty_runs.min()-45, s=f"{empty_run}", ha='center', va='bottom', rotation=90, fontsize=10, fontweight='bold')
  ## plot settings
  axs_empty_runs.set_ylabel("Empty Runs", color='lightcoral', fontweight='bold')
  axs[1].set_title("Validation Results for 5 Cars", fontweight='bold')
  axs[1].set_ylabel("Score", color='skyblue', fontweight='bold')
  axs[1].set_ylim(scores.min() * 0.9, scores.max() * 1.02)
  axs[1].set_xticks(x_positions)
  axs[1].set_xticklabels(labels, ha='center')

  # --- Plot for Car 10 ---
  labels = car10_results["method"] + "_k" + car10_results["k"].astype(str)
  scores = car10_results["score"]
  empty_runs = car10_results["emptyRuns"]
  x_positions = np.arange(len(labels))

  ## scores plot
  axs[2].bar(x_positions - width/2, scores, color='skyblue', width=width)
  for i, score in zip(x_positions, scores):
    axs[2].text(x=i-width/2, y=scores.min()-100, s=f"{score:.2f}", ha='center', va='bottom', rotation=90, fontsize=10, fontweight='bold')

  ## empty runs plot
  axs_empty_runs = axs[2].twinx()
  axs_empty_runs.bar(x_positions + width/2, empty_runs, color='lightcoral', width=width)
  for i, empty_run in zip(x_positions, empty_runs):
    axs_empty_runs.text(x=i+width/2, y=empty_runs.min()-45, s=f"{empty_run}", ha='center', va='bottom', rotation=90, fontsize=10, fontweight='bold')

  ## plot settings
  axs_empty_runs.set_ylabel("Empty Runs", color='lightcoral', fontweight='bold')
  axs[2].set_title("Validation Results for 10 Cars", fontweight='bold')
  axs[2].set_ylabel("Score", color='skyblue', fontweight='bold')
  axs[2].set_ylim(scores.min() * 0.9, scores.max() * 1.02)
  axs[2].set_xticks(x_positions)
  axs[2].set_xticklabels(labels, ha='center')

  # --- Show plot / Save plot ---
  for ax in axs:
      ax.grid(axis='y', linestyle='--', alpha=0.8)
      ax.set_axisbelow(True)
  plt.tight_layout()
  plt.subplots_adjust(hspace=0.3)

  if save:
    plt.savefig(output_path_val_res, dpi=300)
  if show:
    plt.show()

def plot_best_validation_results(show=False, save=False):
  car1_results, car5_results, car10_results = read_validation_results(val_res_path)
  best_car1 = car1_results.loc[car1_results['score'].idxmin()]
  best_car5 = car5_results.loc[car5_results['score'].idxmin()]
  best_car10 = car10_results.loc[car10_results['score'].idxmin()]

  labels = ['1 Car', '5 Cars', '10 Cars']
  best_scores = [best_car1['score'], best_car5['score'], best_car10['score']]
  best_empty_runs = [best_car1['emptyRuns'], best_car5['emptyRuns'], best_car10['emptyRuns']]
  methods = [best_car1['method'] + f"_k{best_car1['k']}" + f" / {labels[0]}",
             best_car5['method'] + f"_k{best_car5['k']}" + f" / {labels[1]}",
             best_car10['method'] + f"_k{best_car10['k']}" + f" / {labels[2]}"]
  x_positions = np.arange(len(labels))
  width = 0.4


  fig, ax = plt.subplots(1, 1, figsize=(8, 8))

  ## score plot
  ax.bar(x_positions - width/2, best_scores, width=width, color='skyblue', label='Best Score')
  for i, score in zip(x_positions, best_scores):
    ax.text(x=i-width/2, y=score/2, s=f"{score:.2f}", ha='center', va='center', rotation=90, fontsize=10, fontweight='bold')

  ## empty runs plot
  ax_empty_runs = ax.twinx()
  ax_empty_runs.bar(x_positions + width/2, best_empty_runs, width=width, color='lightcoral', label='Empty Runs')
  for i, empty_run in zip(x_positions, best_empty_runs):
    ax_empty_runs.text(x=i+width/2, y=empty_run/2, s=f"{empty_run}", ha='center', va='center', rotation=90, fontsize=10, fontweight='bold')

  ## plot settings
  ax_empty_runs.set_ylabel("Empty Runs", color='lightcoral', fontweight='bold')
  ax.set_title("Best Score per Scenario", fontsize=14, fontweight='bold')
  ax.set_ylabel("Best Score", color='skyblue', fontweight='bold')
  ax.grid(axis='y', linestyle='--', alpha=0.5)
  ax.set_axisbelow(True)
  ax.set_ylim(0, max(best_scores) * 1.1)
  ax.set_xticks(x_positions)
  ax.set_xticklabels(methods, ha='center')

  # --- Show plot / Save plot ---
  plt.tight_layout()
  if save:
    plt.savefig(output_path_best_val_res, dpi=300)
  if show:
    plt.show()

