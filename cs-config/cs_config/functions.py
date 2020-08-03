import os

from app import app


def get_version():
    return "hank test"


def get_inputs(meta_param_dict):
    pass


def validate_inputs(meta_param_dict, adjustment, errors_warnings):
    pass


def run_model(meta_param_dict, adjustment):
    pass


def dash():
    app.run_server(
        port=os.environ.get("PORT", 8050),
    )
