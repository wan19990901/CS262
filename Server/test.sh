python -m unittest discover -p "*_test.py"
pip install coverage
coverage run -m unittest discover -p "*_test.py"
coverage html
