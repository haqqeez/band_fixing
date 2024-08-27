#!/bin/bash
#SBATCH --job-name=TASKNAME
#SBATCH --account=def-wilsyl
#SBATCH --time=3:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1000
#SBATCH -o /lustre02/home/haqqeez/SLURMS/OUTNAME-%j.out
#SBATCH --mail-user=MYEMAIL
#SBATCH --mail-type=ALL

module load python/3.11
module load scipy-stack
module load gcc/9.3.0 opencv python scipy-stack

virtualenv --no-download $SLURM_TMPDIR/env
source $SLURM_TMPDIR/env/bin/activate
pip install --no-index --upgrade pip
pip install --no-index seaborn

echo 'running script now'

python band_detect_and_clean.py
