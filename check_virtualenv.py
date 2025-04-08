try:
  import virtualenv
  print("virtualenv is already installed.")
except ImportError:
  print("virtualenv is not installed.")