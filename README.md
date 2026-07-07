# SGC04_LOOPH2

This project developed by researchers at Aerospace Systems Design Laboratory 2025-26 System of Systems Grand Challenge Team, in association with the Georgia Institute of Technology and the Georgia Department of Economic Development Center of Innovation.

For more information, please visit https://www.asdl.gatech.edu/

## Project Abstract
Georgia's reliance on imported conventional gasoline and diesel fuels creates a significant economic risk within its logistical and transportation networks. To stay globally competitive and secure regional economic security, a paradigm shift is required towards localized, sustainable energy generation. Supported by the Georgia Department of Economic Development's Center for Innovation, the Localized Optimization Platform for Hydrogen (LOOP-H2) presents a parametric decision-making tool designed to identify the optimal locations and investments required for new hydrogen infrastructure in Georgia.
 
The LOOP-H2 model evaluates a supply-demand balance, considering multiple technologies as potential hydrogen production drivers, including Levidian Loop technology, Hydrofleet, and Plug Power, against localized demand from industrial truck fleets and warehouse forklifts. An optimization engine drives the model to minimize cost, containing a comprehensive database mapping landfills, distribution centers, Average Annual Daily Traffic (AADT) flows, and major truck stops such as RaceTrac and state-owned fuel centers.
 
Stakeholders interact with the model through an interactive dashboard, allowing rapid trade studies depending on the user's priorities. This dashboard displays the optimized network of hydrogen production locations for development as well as key economic information, including revenue, capital expenses, O&M expenses, and return on investment. Results show that while localized hydrogen production is economically viable, physical network capacities limit transition speeds. To demonstrate this, a baseline scenario was created with an initial 3.5% truck fleet conversion and a 1% annual growth rate. This scenario achieves financial viability but outpaces local hydrogen supply limits by 2030 without additional network investment. Ultimately, LOOP-H2 provides the necessary framework to make informed decisions on the future of a hydrogen-based infrastructure in Georgia.

## Prerequisites
* **Python:** 3.12 or higher.
* **Package Manager:** [Miniconda/Anaconda](https://docs.conda.io/en/latest/miniconda.html) (Recommended) OR standard pip.

---

## Local Development Setup

First, clone the repository to your local machine:
```bash
git clone [https://github.com/thchan99/LOOP-H2](https://github.com/thchan99/LOOP-H2)
cd LOOP-H2
```

### Option A: Conda Environment (Recommended)
Conda is the recommended environment manager for this project to ensure robust handling of scientific computing dependencies.

Create the environment from the YAML file:

```bash
conda env create -f environment.yml
```

Activate the environment:

```bash
conda activate sgc04
```
(Note: If your environment name in the YAML differs, replace sgc04 with the correct name).

Update the environment (Optional):
If new dependencies are added to the environment.yml later, update your local setup using:

```bash
conda env update --file environment.yml --prune
```

### Option B: Python Virtual Environment (pip)
If you prefer a standard Python virtual environment, a requirements.txt file is provided.

Create a virtual environment:

Windows:

```DOS
python -m venv venv
```
macOS/Linux:

```bash
python3 -m venv venv
```
Activate the virtual environment:

Windows:

```DOS
venv\Scripts\activate
```
macOS/Linux:

```bash
source venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application
Once your environment is activated and dependencies are installed, start the local development server:

```bash
python app.py
```

The terminal will display a local address. Open your web browser and navigate to:
http://127.0.0.1:8050/

Project Structure
 + app.py - The main entry point that initializes the Dash server and layout.
 + pages/ - Contains the multi-page application routing and layout files (e.g., Trade Studies).
 + assets/ - Static assets including custom CSS (base.css), JavaScript extensions, and favicon.
 + data/ - Static input parameters, baseline scenario definitions, and geographic shapefiles.
 + model/ & optimization/ - The backend mathematical models and Mixed-Integer Linear Programming (MILP) solvers.
 + output_files/ - Directory for cached solver results and scenario summaries.
 + requirements.txt / environment.yml - Dependency lockfiles for deployment and local setup.