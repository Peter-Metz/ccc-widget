This repository contains a Dash application that compares marginal effective tax rates of the Biden 2020 tax plan to current law, building on TK paper by Pomerleau (2020).

Data for this project are generated using [Cost-of-Capital-Calculator](https://github.com/PSLmodels/Cost-of-Capital-Calculator) and [Tax-Calculator](https://github.com/PSLmodels/Tax-Calculator), open-source projects housed by the Policy Simulation Library. The code that modifies the underlying models to produce the estimates reflected in the application can be found [here](https://github.com/kpomerleau/Cost-of-Capital-Calculator/tree/Tests) and [here](https://github.com/erinmelly/Tax-Calculator/tree/Biden).

The application is hosted at https://ccc-biden.herokuapp.com/.

To run locally:

```
git clone https://github.com/Peter-Metz/ccc-widget
cd ccc-widget
pip install dash
python app.py
```
