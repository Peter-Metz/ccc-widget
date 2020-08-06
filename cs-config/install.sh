ARG=1
git clone https://github.com/hdoupe/ccc-widget
cd ccc-widget
git fetch origin
git checkout hank-cs

conda install pandas plotly pip
pip install dash gunicorn

pip install -e .
