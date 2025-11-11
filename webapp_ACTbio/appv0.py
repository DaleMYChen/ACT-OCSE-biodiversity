from flask import Flask, render_template, jsonify,request, request, make_response, render_template_string, send_from_directory
from firebase_admin import firestore, initialize_app
import json

app = initialize_app(options = {"projectId": "haizea-analytics"})
db = firestore.client(app = app)

app = Flask(__name__,
    static_url_path='/static',  # URL path for static files
    static_folder='static'      # Directory where your static files are
)
# app.secret_key = 'secret2'


# serve images from the img folder
# app.add_url_rule('/img/<path:filename>', endpoint='img', view_func=app.send_static_file)

# app.register_blueprint(login_page)
# app.register_blueprint(product_info_bp)
# app.register_blueprint(account_info)
# app.register_blueprint(lagend_app)
# app.register_blueprint(move_map_app)
# app.register_blueprint(wcs_download_bp)


config = {  #404, 408, 426 and 427
    "veg": {"type": "expression", "expr": "VT=ACTVeg.code@(year=2018)\nNewMap=0*VT\nNewMap=NewMap+(VT==404)*7\nNewMap=NewMap+(VT==408)*5\nNewMap=NewMap+(VT==426)*4\nNewMap=NewMap+(VT==427)*2\nNewMap[NewMap>0]", "cmap": "actmap", "vmin": 0, "vmax": 7},
    "aerial04": {"type": "expression", "expr": "ACTRGB04.red,ACTRGB04.green,ACTRGB04.blue", "cmap": "", "vmin": 0, "vmax": 255},
    "ai04": {"type": "expression", "expr": "AVG=(ACTRGB04.red+ACTRGB04.green+ACTRGB04.blue)/3 \n LC = act_lc_v0_2004.clf[AVG > 5] \n watermask=(ACTVeg.code@(year=2018)==423) \n where(LC,watermask,1)", "cmap": "actmap", "vmin": 0, "vmax": 7},
    "aerial12": {"type": "expression", "expr": "ACTRGB12.red,ACTRGB12.green,ACTRGB12.blue", "cmap": "", "vmin": 0, "vmax": 255},
    "ai12": {"type": "expression", "expr": "AVG=(ACTRGB12.red+ACTRGB12.green+ACTRGB12.blue)/3 \n LC = act_lc_v0_2012_full.clf[AVG > 5] \n watermask=(ACTVeg.code@(year=2018)==423) \n where(LC,watermask,1)", "cmap": "actmap", "vmin": 0, "vmax": 7},
    "aerial15": {"type": "expression", "expr": "ACTRGBI.red,ACTRGBI.green,ACTRGBI.blue", "cmap": "", "vmin": 0, "vmax": 255},
    "ai15": {"type": "expression", "expr": "AVG=(ACTRGBI.red+ACTRGBI.green+ACTRGBI.blue)/3 \n LC = act_lc_v0_2015_full.clf[AVG > 5] \n watermask=(ACTVeg.code@(year=2018)==423) \n where(LC,watermask,1)", "cmap": "actmap", "vmin": 0, "vmax": 7},
    "aerial21": {"type": "expression", "expr": "ACTRGB21.red,ACTRGB21.green,ACTRGB21.blue", "cmap": "", "vmin": 0, "vmax": 255},
    "ai21": {"type": "expression", "expr": "r = ACTRGB21.red \n g = ACTRGB21.green \n b = ACTRGB21.blue \n LC = act_lc_v0_2021.clf[r < 252 & g < 252 & b < 252] \n watermask=(ACTVeg.code@(year=2018)==423) \n where(LC,watermask,1)", "cmap": "actmap", "vmin": 0, "vmax": 7},
    "trend1": {"type": "expression", "expr": "trend(OzWALD.bs@(year=(2004,2008,2012,2016,2020,2023),month=(1,4,8,12))#(year,median))", "cmap": "RdBu_r", "vmin": -2, "vmax": 2},
    "trend2": {"type": "expression", "expr": "trend(OzWALD.pv@(year=(2004,2008,2012,2016,2020,2023),month=(1,4,8,12))#(year,median))", "cmap": "RdBu", "vmin": -3, "vmax": 3},
    "trend3": {"type": "expression", "expr": "red=DEA_GM.red@(year=(2004:2023))\nnir=DEA_GM.nir@(year=(2004:2023))\nndvi=clip((nir-red)/(nir+red),0.1,0.9)\ntrend(ndvi)", "cmap": "RdBu", "vmin": -0.02, "vmax": 0.02},
    "trend4": {"type": "expression", "expr": "trend(OzWALD.lai@(year=(2004,2008,2012,2016,2020,2023),month=(1,4,8,12))#(year,median))", "cmap": "RdBu", "vmin": -0.15, "vmax": 0.15},
    "trend5": {"type": "expression", "expr": "trend(OzWALD.gpp@(year=(2004,2008,2012,2016,2020,2023),month=(1,4,8,12))#(year,median))", "cmap": "RdBu", "vmin": -0.2, "vmax": 0.2},
    "trend6": {"type": "expression", "expr": "trend(WCF.wcf@(year=(2004:2023))#(year,median))", "cmap": "RdBu", "vmin": -2.5, "vmax": 2.5},
    "none": {"type": "expression", "expr": "", "cmap": "", "vmin": 0, "vmax": 0},
    "satellite": {
        "type": "tile",
        "url": "http://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}",
        "attribution": "© Google Maps"
    },
    "district-boundaries": {
        "type": "geojson",
        "path": "actgov_districts.geojson",
        "style": {
            "color": "#228B22",  # Forest green color
            "weight": 2,
            "opacity": 0.65,
            "fillOpacity": 0.8
        }
    },
}


@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/logout')
def logout():
    resp = make_response(jsonify({"message": "Logout successful"}, 200))
    resp.headers['HX-Redirect'] = '/'
    return resp

@app.route('/main')
def main():
    user = get_user_info(request.headers["uid"])
    # Avoid changing url
    response = make_response(render_template('index.html', user=user))
    response.headers['HX-Push-Url'] = "false"
    return response

def get_user_info(uid):
    print(uid)
    doc = db.collection('users').where('uid', '==', uid).get()
    if doc:
        info = doc[0].to_dict()
        print(info)
        name = info["email"].split('@')[0].capitalize()
        initial = name[0]
        info.update({'name': name, 'initial': initial})
        return info
    else:
        return None

# Add new endpoint to serve GeoJSON files
@app.route('/static/<path:filename>')
def serve_geojson(filename):
    try:
        # Assuming GeoJSON files are stored in a 'static/geojson' directory
        return send_from_directory('static/geojson', filename)
    except FileNotFoundError:
        return jsonify({"error": "GeoJSON file not found"}), 404

@app.route('/update-left-layer', methods=['POST'])
def update_left_layer():
    layer = request.form.get("left-layer")
    layer_config = config[layer]
    
    if layer_config["type"] == "expression":
        return jsonify({
            'type': 'expression',
            'expression': layer_config["expr"],
            'cmap': layer_config["cmap"],
            'vmin': layer_config["vmin"],
            'vmax': layer_config["vmax"],
        })
    elif layer_config["type"] == "tile":
        return jsonify({
            'type': 'tile',
            'url': layer_config["url"],
            'attribution': layer_config["attribution"]
        })

    elif layer_config["type"] == "geojson":
        return jsonify({
            'type': 'geojson',
            'url': f'/static/{layer_config["path"]}',
            'style': layer_config["style"]
        })

# Update the right layer route similarly
@app.route('/update-right-layer', methods=['POST'])
def update_right_layer():
    layer = request.form.get("right-layer")
    layer_config = config[layer]
    
    if layer_config["type"] == "expression":
        return jsonify({
            'type': 'expression',
            'expression': layer_config["expr"],
            'cmap': layer_config["cmap"],
            'vmin': layer_config["vmin"],
            'vmax': layer_config["vmax"],
        })
    elif layer_config["type"] == "tile":
        return jsonify({
            'type': 'tile',
            'url': layer_config["url"],
            'attribution': layer_config["attribution"]
        })

    elif layer_config["type"] == "geojson":
        return jsonify({
            'type': 'geojson',
            'url': f'/static/{layer_config["path"]}',
            'style': layer_config["style"]
        })

@app.route('/colour_palette', methods=['POST'])
def colour_palette():
    layer = request.form.get("left-layer") or request.form.get("right-layer")
    # RGB legend for aerial photography

    if layer.startswith('aerial'):
        return render_template_string("""
            <div class="bg-slate-800 p-4 rounded-md">
                <p class="mb-2 text-white">RGB Composite</p>
                <div class="flex items-center gap-2 mb-2">
                    <div class="w-4 h-4 bg-red-500"></div>
                    <span class="text-white text-sm">Red Band</span>
                </div>
                <div class="flex items-center gap-2 mb-2">
                    <div class="w-4 h-4 bg-green-500"></div>
                    <span class="text-white text-sm">Green Band</span>
                </div>
                <div class="flex items-center gap-2">
                    <div class="w-4 h-4 bg-blue-500"></div>
                    <span class="text-white text-sm">Blue Band</span>
                </div>
            </div>
        """)
    elif layer.startswith('veg'):
            return render_template_string("""
                <div class="bg-slate-800 p-4 rounded-md">
                    <p class="mb-4 text-white">Vegetation Classes</p>
                    <div class="space-y-2">
                        <div class="flex items-center gap-2">
                            <div class="w-4 h-4" style="background-color: #006400"></div>
                            <span class="text-white text-sm">Box gum grassy woodland</span>
                        </div>
                        <div class="flex items-center gap-2">
                            <div class="w-4 h-4" style="background-color: #90EE90"></div>
                            <span class="text-white text-sm">Natural temperate grassland</span>
                        </div>
                        <div class="flex items-center gap-2">
                            <div class="w-4 h-4" style="background-color: #E6E8A1"></div>
                            <span class="text-white text-sm">Urban open space</span>
                        </div>
                        <div class="flex items-center gap-2">
                            <div class="w-4 h-4" style="background-color: #C0C0C0"></div>
                            <span class="text-white text-sm">Urban and developed areas</span>
                        </div>
                    </div>
                </div>
            """)
    # RdBu_r legend for trend analysis
    elif layer.startswith('trend'):
        # Calculate stops based on vmin and vmax
        # For RdBu_r, we want to ensure 0 is always in the middle
        vmin = config[layer]["vmin"]
        vmax = config[layer]["vmax"]
        cmap = config[layer]["cmap"]
        max_abs = max(abs(vmin), abs(vmax))
        
        # Create color stops that are proportional to the actual values
        base_color_stops = [
            {"color": "#67001F", "value": max_abs},       # Darkest red - highest positive
            {"color": "#B2182B", "value": max_abs * 0.6}, # Medium red
            {"color": "#F4A582", "value": max_abs * 0.2}, # Light red
            {"color": "#F7F7F7", "value": 0},            # White/neutral at zero
            {"color": "#92C5DE", "value": -max_abs * 0.2}, # Light blue
            {"color": "#2166AC", "value": -max_abs * 0.6}, # Medium blue
            {"color": "#053061", "value": -max_abs}        # Darkest blue - lowest negative
        ]
        
        # If it's trend1, reverse the color stops, otherwise use the base stops
        if layer == 'trend1':
            color_stops = list(reversed(base_color_stops))
            # Need to negate the values when reversing to maintain correct mapping
            for stop in color_stops:
                stop["value"] = -stop["value"]
        else:
            color_stops = base_color_stops
        
        # Sort the stops by value to ensure correct gradient order
        color_stops.sort(key=lambda x: x["value"])

        # Convert values to percentages for the gradient
        value_range = max_abs * 2  # Total range from -max_abs to +max_abs
        gradient_stops = []
        for stop in color_stops:
            # Convert value to percentage position in gradient
            percentage = ((stop["value"] + max_abs) / value_range) * 100
            gradient_stops.append(f"{stop['color']} {percentage:.1f}%")

        gradient_string = ", ".join(gradient_stops)
        
        # Create tick marks at significant points
        tick_marks = [
            {"position": "top", "value": vmax},
            {"position": "center", "value": 0},
            {"position": "bottom", "value": vmin}
        ]

        return render_template_string("""
            <div class="bg-slate-800 p-4 rounded-md">
                <p class="mb-4 text-white">Trend Analysis</p>
                <div class="flex items-center gap-4">
                    <!-- Gradient bar -->
                    <div class="w-8 h-64 rounded overflow-hidden">
                        <div class="w-full h-full" style="background: linear-gradient(to bottom, {{ gradient }});"></div>
                    </div>
                    
                    <!-- Value and tick marks container -->
                    <div class="relative h-64">
                        {% for tick in tick_marks %}
                        <div class="absolute 
                            {% if tick.position == 'top' %}top-0
                            {% elif tick.position == 'center' %}top-1/2
                            {% else %}bottom-0{% endif %} 
                            flex items-center">
                            <div class="w-2 h-px bg-white"></div>
                            <span class="ml-2 text-white text-sm">{{ '%0.2f'|format(tick.value) }}</span>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        """, 
        gradient=gradient_string,
        tick_marks=tick_marks
        )
    # Default AI mapping legend
    elif layer.startswith('ai'):
        legend_items = [
            {"color": "#FFFFFF", "label": "Unknown"},
            {"color": "#4169E1", "label": "Water"},
            {"color": "#C0C0C0", "label": "Unvegetated surface"},
            {"color": "#808080", "label": "Building"},
            {"color": "#E6E8A1", "label": "Sparse short vegetation"},
            {"color": "#90EE90", "label": "Dense short vegetation"},
            {"color": "#228B22", "label": "Shrubs and tall forbs"},
            {"color": "#006400", "label": "Tree"}
        ]
        
        return render_template_string("""
            <div class="bg-slate-800 p-4 rounded-md">
                <p class="mb-2 text-white">Land Classification</p>
                <div class="space-y-2">
                    {% for item in legend_items %}
                    <div class="flex items-center gap-2">
                        <div class="w-4 h-4 border border-gray-600" style="background-color: {{ item.color }}"></div>
                        <span class="text-white text-sm">{{ item.label }}</span>
                    </div>
                    {% endfor %}
                </div>
            </div>
        """, legend_items=legend_items)
    
    # Default state or unrecognized layer type
    else:
        return render_template_string("""
            <div class="bg-slate-800 p-4 rounded-md">
                <p class="text-white">Select a layer to view legend</p>
            </div>
        """)

@app.route('/load-geojson', methods=['POST'])
def load_geojson():
    with open('static/actgov_districts.geojson') as f:
        dist = json.load(f)
    with open('static/actgov_division_full.geojson') as f:
        div = json.load(f)

    payload = {
        "type": "geojson",
        "district": dist,
        "division": div,
        "style_dist": {
            # Dark grey
            "color": "#141414",  
            "weight": 2,
            "opacity": 1,
            "fillOpacity": 0
        },
        "style_div": {
            # Vibrant purple
            "color": "#AD03DE",
            "weight": 2,
            "opacity": 1,
            "fillOpacity": 0
        }
    }
    return jsonify(payload)

if __name__ == '__main__':
    app.run(debug=True)
