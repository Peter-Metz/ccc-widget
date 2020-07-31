# Write or import your Compute Studio functions here.
from app import app


def get_version():
    return "hank test"


def get_inputs(meta_param_dict):
    pass


def validate_inputs(meta_param_dict, adjustment, errors_warnings):
    pass


def run_model(meta_param_dict, adjustment):
    pass


if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=True)
