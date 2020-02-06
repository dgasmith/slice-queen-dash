import os
import uuid
from datetime import timedelta

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

from dash.dependencies import Input, Output

from flask import session
from flask_caching import Cache

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.PULSE])
server = app.server
server.config["SECRET_KEY"] = str(os.urandom(16))
app.config.suppress_callback_exceptions = True


@server.before_request
def make_session_permanent():
    session.permanent = True


#    server.permanent_session_lifetime = timedelta(minutes=5)


cache = Cache(server, config={"CACHE_TYPE": "simple"})

slices = [
    "Plain Jane Slice",
    "Italian seasoned crust, tomato sauce, whole milk Mozzarella, fresh basil.",
    "Prom Queen Margherita Slice",
    "Tomato garlic crust, tomato sauce, fresh Mozzarella, charred pepperoni, and pesto.",
    "Frankie Fun Guy Slice",
    "Rosemary apricot crust, roasted mushroom cream, pepperoni, beer mushrooms, chives.",
    "Hokie Hangover Slice",
    "Pumpkin spice crust, turkey, sausage stuffing, fries, biscuit gravy, and hokie sauce.",
    "Foreign Exchange Slice",
    "Maple syrup, chicken, blueberry cream cheese, waffle pieces, and bacon.",
    "Sup Dude Slice",
    "Pineapple upside down crust ham, bacon and pineapple salsa, orange-ginger glaze, cilantro.",
    "Just Blaze Slice",
    "Bacon and Blue cheese crust, Buffalo chicken dip, pickled chilis, sun-dried tomato ranch.",
    "Veggie Voodoo Slice",
    "Sun-dried tomato pesto crust, roasted garlic Ricotta, roasted veggies, and balsamic glaze.",
    "Philly Special Slice",
    "Rosemary-sage crust, steak, onions, peppers, mushrooms, and beer cheese.",
    "Dorm Gourm Slice",
    "Sriracha crust, ramen sauce, chicken, noodles, veggies, sesame seeds, hot honey.",
    "Ghost Toast Slice",
    "Cilantro-lime crust, avocado, fried egg, Sriracha and ghost pepper aioli.",
]

slices = [
    {"name": slices[x * 2], "desc": slices[x * 2 + 1]} for x in range(len(slices) // 2)
]

# Navbar header
navbar = dbc.NavbarSimple(
    children=[dbc.NavItem(dbc.NavLink("Results", href="/results"))],
    color="primary",
    dark=True,
    brand="Slice Queen",
    brand_href="/",
    sticky="top",
)


# Slices
choices = []
for sl in slices:

    uid = sl["name"].replace(" ", "-")
    plus_id = uid + "-plus"
    minus_id = uid + "-minus"

    card = dbc.Card(
        dbc.CardBody(
            [
                html.H5(sl["name"], className="card-title"),
                html.P(sl["desc"]),
                html.Div(
                    [
                        dbc.Button(0, color="primary", id=uid),
                        dbc.Button("Plus", color="success", id=plus_id),
                        dbc.Button("Minus", color="danger", id=minus_id),
                    ]
                ),
            ]
        ),
        className="border-primary",
    )
    choices.append(card)


index_page = html.Div(
    [
        dbc.Row(dbc.CardColumns(choices, className="mb-4")),
        dbc.Row(
            [
                dbc.Card(
                    [
                        html.P(
                            "Each slice is about 5 x 5 inches, we normally recommend two slices.",
                            className="text-center",
                        ),
                    ],
                    style={"width": "100%"},
                    color="primary",
                    inverse=True,
                    className="border-secondary",
                )
            ],
            className="mb-4",
        ),
    ]
)
index_page = dbc.Container(index_page)

# app.layout = html.Div([navbar, body])
app.layout = html.Div(
    [navbar, dcc.Location(id="url", refresh=False), html.Div(id="page-content")]
)


def build_callback(uid):

    uid = sl["name"].replace(" ", "-")
    plus_id = uid + "-plus"
    minus_id = uid + "-minus"

    @app.callback(
        Output(uid, "children"),
        [Input(plus_id, "n_clicks_timestamp"), Input(minus_id, "n_clicks_timestamp")],
    )
    def clicker(plus, minus):
        plus = plus or 0
        minus = minus or 0

        if "uuid" not in session:
            session["uuid"] = str(uuid.uuid4())

        value = session.get(uid, 0)
        if (plus + minus) > 0:
            if plus > minus:
                value += 1
            else:
                value -= 1

        if value < 0:
            value = 0

        session[uid] = value
        data = {k: v for k, v in session.items()}

        cache.set(data["uuid"], data)
        session.modified = True

        users = cache.get("users")
        if users is None:
            users = set()
        if data["uuid"] not in users:
            users.add(data["uuid"])
            cache.set("users", users)
            print("new user", users)

        return value


for sl in slices:
    build_callback(sl["name"])

results = dbc.Container([html.Div(id="results-trigger"), dcc.Graph(id="results-graph")])


@app.callback(Output("results-graph", "figure"), [Input("results-trigger", "id")])
def build_graph(id):

    data = {"data": [], "layout": {"title": "Slices to Order"}}
    users = cache.get("users")
    if users is None:
        return data

    users = list(users)
    output = cache.get(users[0])
    for u in users[1:]:
        counts = cache.get(u)
        for k, v in counts.items():
            output[k] += v

    output.pop("uuid")
    output.pop("_permanent")

    x, y = [], []
    for k, v in output.items():
        x.append(k)
        y.append(v)

    data["data"] = [{"x": x, "y": y, "type": "bar", "name": "SF"}]
    return data


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def display_page(pathname):
    if pathname == "/results":
        return results
    else:
        return index_page


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run_server(debug=True, port=port)
