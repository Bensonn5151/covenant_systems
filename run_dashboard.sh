#!/bin/bash
# Covenant Systems - Dashboard Launcher
#
# Launches the Streamlit dashboard with proper environment variables
# to prevent FAISS segmentation faults on macOS

# Set threading environment variables
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export KMP_DUPLICATE_LIB_OK=TRUE

# Navigate to dashboard directory
cd "$(dirname "$0")/dashboard"

# Launch Streamlit
echo "Launching Covenant Systems Dashboard..."
echo "📊 Dashboard will open in your browser at http://localhost:8501"
echo ""

streamlit run app.py
