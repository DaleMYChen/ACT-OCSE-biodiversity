from flask import Flask, render_template, jsonify, request, make_response, render_template_string, send_from_directory
from firebase_admin import firestore, initialize_app
import json

app = initialize_app(options={"projectId": "haizea-analytics"})
db = firestore.client(app=app)

app = Flask(__name__,
    static_url_path='/static',
    static_folder='static'
)

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
    # Pass both user and variables to the template
    response = make_response(render_template('index.html', user=user, variables=variables))
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


# Updated configuration structure for tiered dropdowns
variables = {
    "vegetation_types": {
        "display": "Vegetation types",
        "years": ["map"],
        "default_year": "map",
        "configs": {
            "map": {
                "type": "expression",
                "expr": "VT=ACTVeg.code@(year=2018)\nNewMap=0*VT\nNewMap=NewMap+(VT==404)*7\nNewMap=NewMap+(VT==408)*5\nNewMap=NewMap+(VT==426)*4\nNewMap=NewMap+(VT==427)*2\nNewMap[NewMap>0]",
                "cmap": "actmap",
                "vmin": 0,
                "vmax": 7
            }
        }
    },
    "aerial": {
        "display": "Aerial imagery",
        "years": ["2004", "2012", "2015", "2021", "2023"],
        "default_year": "2021",
        "configs": {
            "2004": {
                "type": "expression",
                "expr": "ACTRGB04.red,ACTRGB04.green,ACTRGB04.blue",
                "cmap": "",
                "vmin": 0,
                "vmax": 255
            },
            "2012": {
                "type": "expression",
                "expr": "ACTRGB12.red,ACTRGB12.green,ACTRGB12.blue",
                "cmap": "",
                "vmin": 0,
                "vmax": 255
            },
            "2015": {
                "type": "expression",
                "expr": "ACTRGBI.red,ACTRGBI.green,ACTRGBI.blue",
                "cmap": "",
                "vmin": 0,
                "vmax": 255
            },
            "2021": {
                "type": "expression",
                "expr": "ACTRGB21.red,ACTRGB21.green,ACTRGB21.blue",
                "cmap": "",
                "vmin": 0,
                "vmax": 255
            },
            "2023": {
                "type": "expression",
                "expr": "ACTRGB23.red,ACTRGB23.green,ACTRGB23.blue",
                "cmap": "",
                "vmin": 0,
                "vmax": 255
            }
        }
    },
    "landcover": { 
        "display": "Land cover",
        "years": ["2004", "2012", "2015", "2021", "2023"],
        "default_year": "2021",
        "configs": {
            "2004": {
                "type": "expression",
                "expr": "AVG=(ACTRGB04.red+ACTRGB04.green+ACTRGB04.blue)/3 \n LC = act_lc_v0_2004.clf[AVG > 5] \n watermask=(ACTVeg.code@(year=2018)==423) \n where(LC,watermask,1)",
                "cmap": "actmap",
                "vmin": 0,
                "vmax": 7
            },
            "2012": {
                "type": "expression",
                "expr": "AVG=(ACTRGB12.red+ACTRGB12.green+ACTRGB12.blue)/3 \n LC = act_lc_v0_2012_full.clf[AVG > 5] \n watermask=(ACTVeg.code@(year=2018)==423) \n where(LC,watermask,1)",
                "cmap": "actmap",
                "vmin": 0,
                "vmax": 7
            },
            "2015": {
                "type": "expression",
                "expr": "AVG=(ACTRGBI.red+ACTRGBI.green+ACTRGBI.blue)/3 \n LC = act_lc_v0_2015_full.clf[AVG > 5] \n watermask=(ACTVeg.code@(year=2018)==423) \n where(LC,watermask,1)",
                "cmap": "actmap",
                "vmin": 0,
                "vmax": 7
            },
            "2021": {
                "type": "expression",
                "expr": "r = ACTRGB21.red \n g = ACTRGB21.green \n b = ACTRGB21.blue \n LC = act_lc_v0_2021.clf[r < 252 & g < 252 & b < 252] \n watermask=(ACTVeg.code@(year=2018)==423) \n where(LC,watermask,1)",
                "cmap": "actmap",
                "vmin": 0,
                "vmax": 7
            },
            "2023": {
                "type": "expression",
                "expr": "LC = act_lc_v2_2023.clf \n watermask=(ACTVeg.code@(year=2018)==423) \n where(LC,watermask,1)",
                "cmap": "actmap",  
                "vmin": 0,
                "vmax": 7
            }
        }
    }, 

    "bs": {
        "display": "Unprotected soil (%)",
        "years": ["trend (2004-2023)", "2004", "2015", "2021"],
        "default_year": "trend (2004-2023)",
        "configs": {
            "trend (2004-2023)": {
                "type": "expression",
                "expr": "map = trend(OzWALD.bs@(year=(2004:2023))#(year,mean))\n watermask=(ACTVeg.code@(year=2018)==423) \n whereNan(map,watermask)",
                "cmap": "RdBu_r",
                "vmin": -2,
                "vmax": 2,
                "continuous": True
            },
            "2004": {
                "type": "expression",
                "expr": "map = OzWALD.bs@(year=(2004),month=(1,4,8,12))#(year,mean)\n watermask=(ACTVeg.code@(year=2018)==423) \n whereNan(map,watermask)",
                "cmap": "BrBG_r",
                "vmin": 0,
                "vmax": 100,
                "continuous": True
            },
            "2015": {
                "type": "expression",
                "expr": "map = OzWALD.bs@(year=(2015),month=(1,4,8,12))#(year,mean)\n watermask=(ACTVeg.code@(year=2018)==423) \n whereNan(map,watermask)",
                "cmap": "BrBG_r",
                "vmin": 0,
                "vmax": 100,
                "continuous": True
            },
            "2021": {
                "type": "expression",
                "expr": "map = OzWALD.bs@(year=(2021),month=(1,4,8,12))#(year,mean)\n watermask=(ACTVeg.code@(year=2018)==423) \n whereNan(map,watermask)",
                "cmap": "BrBG_r",
                "vmin": 0,
                "vmax": 100,
                "continuous": True
            }
        }
    },

    "pv": {
        "display": "Vegetation cover (%)",
        "years": ["trend (2004-2023)", "2004", "2015", "2021"],
        "default_year": "trend (2004-2023)",
        "configs": {
            "trend (2004-2023)": {
                "type": "expression",
                "expr": "map = trend(OzWALD.pv@(year=(2004:2023))#(year,mean))\n watermask=(ACTVeg.code@(year=2018)==423) \n whereNan(map,watermask)",
                "cmap": "RdBu",
                "vmin": -3,
                "vmax": 3,
                "continuous": True
            },
            "2004": {
                "type": "expression",
                "expr": "map = OzWALD.pv@(year=(2004),month=(1,4,8,12))#(year,mean)\n watermask=(ACTVeg.code@(year=2018)==423) \n whereNan(map,watermask)",
                "cmap": "BrBG",
                "vmin": 0,
                "vmax": 100,
                "continuous": True
            },
            "2015": {
                "type": "expression",
                "expr": "map = OzWALD.pv@(year=(2015),month=(1,4,8,12))#(year,mean)\n watermask=(ACTVeg.code@(year=2018)==423) \n whereNan(map,watermask)",
                "cmap": "BrBG",
                "vmin": 0,
                "vmax": 100,
                "continuous": True
            },
            "2021": {
                "type": "expression",
                "expr":  "map = OzWALD.pv@(year=(2021),month=(1,4,8,12))#(year,mean)\n watermask=(ACTVeg.code@(year=2018)==423) \n whereNan(map,watermask)",
                "cmap": "BrBG",
                "vmin": 0,
                "vmax": 100,
                "continuous": True
            }
        }
    },

    "ndvi": {
        "display": "Vegetation greenness (NDVI)",
        "years": ["trend (2004-2023)", "2004", "2015", "2021"],
        "default_year": "trend (2004-2023)",
        "configs": {
            "trend (2004-2023)": {
                "type": "expression",
                "expr": "red=DEA_GM.red@(year=(2004:2023))\nnir=DEA_GM.nir@(year=(2004:2023))\nndvi=clip((nir-red)/(nir+red),0.1,0.9)\nmap=trend(ndvi)\n watermask=(ACTVeg.code@(year=2018)==423) \n whereNan(map,watermask)",
                "cmap": "RdBu",
                "vmin": -0.02,
                "vmax": 0.02,
                "continuous": True
            },
            "2004": {
                "type": "expression",  
                "expr": "red=DEA_GM.red@(year=2004)#(year,mean)\nnir=DEA_GM.nir@(year=2004)#(year,mean)\nndvi=clip((nir-red)/(nir+red),0.1,0.8)\n watermask=(ACTVeg.code@(year=2018)==423) \n whereNan(ndvi,watermask)",
                "cmap": "BrBG",
                "vmin": 0.1,
                "vmax": 0.8,
                "continuous": True
            },
            "2015": {
                "type": "expression",
                "expr": "red=DEA_GM.red@(year=2015)#(year,mean)\nnir=DEA_GM.nir@(year=2015)#(year,mean)\nndvi=clip((nir-red)/(nir+red),0.1,0.8)\nwatermask=(ACTVeg.code@(year=2018)==423) \n whereNan(ndvi,watermask)",
                "cmap": "BrBG",
                "vmin": 0.1,
                "vmax": 0.8,
                "continuous": True
            },
            "2021": {
                "type": "expression",
                "expr": "red=DEA_GM.red@(year=2021)#(year,mean)\nnir=DEA_GM.nir@(year=2021)#(year,mean)\nndvi=clip((nir-red)/(nir+red),0.1,0.8)\nwatermask=(ACTVeg.code@(year=2018)==423) \n whereNan(ndvi,watermask)",
                "cmap": "BrBG",
                "vmin": 0.1,
                "vmax": 0.8,
                "continuous": True
            }
        }
    },

    "lai": {
        "display": "Leaf area (LAI)",
        "years": ["trend (2004-2023)", "2004", "2015", "2021"],
        "default_year": "trend (2004-2023)",
        "configs": {
            "trend (2004-2023)": {
                "type": "expression",
                "expr": "map = trend(OzWALD.lai@(year=(2004:2023))#(year,mean))\n watermask=(ACTVeg.code@(year=2018)==423) \n whereNan(map,watermask)",
                "cmap": "RdBu",
                "vmin": -0.15,
                "vmax": 0.15,
                "continuous": True
            },
            "2004": {
                "type": "expression",
                "expr": "map = OzWALD.lai@(year=(2004),month=(1,4,8,12))#(year,mean)\n watermask=(ACTVeg.code@(year=2018)==423) \n whereNan(map,watermask)",
                "cmap": "BrBG",
                "vmin": 0,
                "vmax": 5,
                "continuous": True
            },
            "2015": {
                "type": "expression",
                "expr": "map = OzWALD.lai@(year=(2015),month=(1,4,8,12))#(year,mean)\n watermask=(ACTVeg.code@(year=2018)==423) \n whereNan(map,watermask)",
                "cmap": "BrBG",
                "vmin": 0,
                "vmax": 5,
                "continuous": True
            },
            "2021": {
                "type": "expression",
                "expr": "map = OzWALD.lai@(year=(2021),month=(1,4,8,12))#(year,mean)\n watermask=(ACTVeg.code@(year=2018)==423) \n whereNan(map,watermask)",
                "cmap": "BrBG",
                "vmin": 0,
                "vmax": 5,
                "continuous": True
            }
        }
    },

    "gpp": {
        "display": "Growth rate (gC/m2/d)",
        "years": ["trend (2004-2023)", "2004", "2015", "2021"],
        "default_year": "trend (2004-2023)",
        "configs": {
            "trend (2004-2023)": {
                "type": "expression",
                "expr": "map = trend(OzWALD.gpp@(year=(2004:2023))#(year,mean))\n watermask=(ACTVeg.code@(year=2018)==423) \n whereNan(map,watermask)",
                "cmap": "RdBu",
                "vmin": -0.2,
                "vmax": 0.2,
                "continuous": True
            },
            "2004": {
                "type": "expression",
                "expr": "map = OzWALD.gpp@(year=(2004),month=(1,4,8,12))#(year,mean)\n watermask=(ACTVeg.code@(year=2018)==423) \n whereNan(map,watermask)",
                "cmap": "BrBG",
                "vmin": 0,
                "vmax": 6,
                "continuous": True
            },
            "2015": {
                "type": "expression",
                "expr": "map = OzWALD.gpp@(year=(2015),month=(1,4,8,12))#(year,mean)\n watermask=(ACTVeg.code@(year=2018)==423) \n whereNan(map,watermask)",
                "cmap": "BrBG",
                "vmin": 0,
                "vmax": 6,
                "continuous": True
            },
            "2021": {
                "type": "expression",
                "expr": "map = OzWALD.gpp@(year=(2021),month=(1,4,8,12))#(year,mean)\n watermask=(ACTVeg.code@(year=2018)==423) \n whereNan(map,watermask)",
                "cmap": "BrBG",
                "vmin": 0,
                "vmax": 6,
                "continuous": True
            }
        }
    },

    "wcf": {
        "display": "Woody canopy cover (%)",
        "years": ["trend (2004-2023)", "2004", "2015", "2021"],
        "default_year": "trend (2004-2023)",
        "configs": {
            "trend (2004-2023)": {
                "type": "expression",
                "expr": "map = trend(WCF.wcf@(year=(2004:2023))#(year,mean))\n watermask=(ACTVeg.code@(year=2018)==423) \n whereNan(map,watermask)",
                "cmap": "RdBu",
                "vmin": -2.5,
                "vmax": 2.5,
                "continuous": True
            },
            "2004": {
                "type": "expression", 
                "expr": "map = WCF.wcf@(year=(2004),month=(1,4,8,12))#(year,mean)\n watermask=(ACTVeg.code@(year=2018)==423) \n whereNan(map,watermask)",
                "cmap": "BrBG",
                "vmin": 0,
                "vmax": 60,
                "continuous": True
            },
            "2015": {
                "type": "expression",
                "expr": "map = WCF.wcf@(year=(2015),month=(1,4,8,12))#(year,mean)\n watermask=(ACTVeg.code@(year=2018)==423) \n whereNan(map,watermask)",
                "cmap": "BrBG",
                "vmin": 0,
                "vmax": 60,
                "continuous": True
            },
            "2021": {
                "type": "expression",
                "expr": "map = WCF.wcf@(year=(2021),month=(1,4,8,12))#(year,mean)\n watermask=(ACTVeg.code@(year=2018)==423) \n whereNan(map,watermask)",
                "cmap": "BrBG",
                "vmin": 0,
                "vmax": 60,
                "continuous": True
            }
        }
    },
}

@app.route('/get-years/<side>')
def get_years(side):
    print("\n=== Get Years Request ===")
    variable = request.args.get(f'{side}-variable')
    print(f"Side: {side}")
    print(f"Variable requested: {variable}")
    
    if variable not in variables:
        print(f"Error: Invalid variable {variable}")
        return "Invalid variable", 400
        
    years = variables[variable]['years']
    default_year = variables[variable]['default_year']
    print(f"Available years: {years}")
    print(f"Default year: {default_year}")
    
    return render_template_string("""
        <select
            class="w-full bg-slate-700 border border-slate-600 rounded-md p-2"
            name="{{ side }}-year"
            hx-post="/update-{{ side }}-layer"
            hx-target="#{{ side }}-map"
            hx-trigger="load, change"
            hx-include="[name='{{ side }}-variable']"
        >
            {% for year in years %}
            <option value="{{ year }}" {% if year == default_year %}selected{% endif %}>
                {{ year }}
            </option>
            {% endfor %}
        </select>
    """, side=side, years=years, default_year=default_year)



@app.route('/update-left-layer', methods=['POST'])
def update_left_layer():
    print("\n=== Update Left Layer Request ===")
    print(f"Form data: {request.form}")
    
    variable = request.form.get('left-variable')
    year = request.form.get('left-year')
    
    print(f"Variable: {variable}")
    print(f"Year: {year}")
    
    if not variable:
        print("Error: No variable provided")
        return jsonify({'error': 'No variable provided'}), 400
        
    if not year:
        print("Error: No year provided")
        return jsonify({'error': 'No year provided'}), 400
    
    if variable not in variables:
        print(f"Error: Invalid variable {variable}")
        return jsonify({'error': 'Invalid variable'}), 400
        
    var_config = variables[variable]['configs'].get(year)
    if not var_config:
        print(f"Error: Invalid year {year} for variable {variable}")
        return jsonify({'error': 'Invalid year for variable'}), 400
    
    print("Configuration found:")
    print(f"  Type: {var_config.get('type')}")
    print(f"  Expression: {var_config.get('expr')[:50]}...")
    print(f"  Colormap: {var_config.get('cmap')}")
    print(f"  vmin: {var_config.get('vmin')}")
    print(f"  vmax: {var_config.get('vmax')}")
    
    response = {
        'type': "expression",
        'expression': var_config["expr"],
        'cmap': var_config["cmap"],
        'vmin': var_config["vmin"],
        'vmax': var_config["vmax"]
    }
    
    print(f"Sending response: {response}")
    return jsonify(response)


@app.route('/update-right-layer', methods=['POST'])
def update_right_layer():
    print("\n=== Update Right Layer Request ===")
    print(f"Form data: {request.form}")
    
    variable = request.form.get('right-variable')
    year = request.form.get('right-year')
    
    print(f"Variable: {variable}")
    print(f"Year: {year}")
    
    if not variable:
        print("Error: No variable provided")
        return jsonify({'error': 'No variable provided'}), 400
        
    if not year:
        print("Error: No year provided")
        return jsonify({'error': 'No year provided'}), 400
    
    if variable not in variables:
        print(f"Error: Invalid variable {variable}")
        return jsonify({'error': 'Invalid variable'}), 400
        
    var_config = variables[variable]['configs'].get(year)
    if not var_config:
        print(f"Error: Invalid year {year} for variable {variable}")
        print(f"Available years for {variable}: {variables[variable]['years']}")
        print(f"Available configs: {list(variables[variable]['configs'].keys())}")
        return jsonify({'error': 'Invalid year for variable'}), 400
    
    print("Configuration found:")
    print(f"  Type: {var_config.get('type')}")
    print(f"  Expression: {var_config.get('expr')[:50]}...")  # Print first 50 chars of expression
    print(f"  Colormap: {var_config.get('cmap')}")
    print(f"  vmin: {var_config.get('vmin')}")
    print(f"  vmax: {var_config.get('vmax')}")
    
    # Handle different types of layers
    if var_config["type"] == "expression":
        response = {
            'type': 'expression',
            'expression': var_config["expr"],
            'cmap': var_config["cmap"],
            'vmin': var_config["vmin"],
            'vmax': var_config["vmax"]
        }
    elif var_config["type"] == "tile":
        response = {
            'type': 'tile',
            'url': var_config["url"],
            'attribution': var_config.get("attribution", "")
        }
    else:
        print(f"Error: Unknown configuration type: {var_config['type']}")
        return jsonify({'error': 'Invalid configuration type'}), 400
    
    print(f"Sending response: {response}")
    return jsonify(response)


@app.route('/colour_palette', methods=['POST'])
def colour_palette():
    # Debug: Log incoming request data
    print("=== Colour Palette Request ===")
    print(f"Form data: {request.form}")
    
    side = 'left' if request.form.get('left-variable') else 'right'
    variable = request.form.get(f'{side}-variable')
    year = request.form.get(f'{side}-year')
    
    print(f"Side: {side}")
    print(f"Variable: {variable}")
    print(f"Year: {year}")
    
    if not variable:
        print("No variable selected, returning default template")
        return render_template_string("""
            <div class="bg-slate-800 p-4 rounded-md">
                <p class="text-white">Select a layer to view legend</p>
            </div>
        """)

    if not year and variable in variables:
        year = variables[variable]['default_year']
        print(f"No year provided, using default year: {year}")

    title = variables[variable]['display']
    print(f"Variable display title: {title}")
    
    try:
        config = variables[variable]['configs'][year]
        print(f"Config for {variable} - {year}:")
        print(f"  Type: {config.get('type')}")
        print(f"  Expression: {config.get('expr')[:50]}...")  # Print first 50 chars of expression
        print(f"  Colormap: {config.get('cmap')}")
        print(f"  vmin: {config.get('vmin')}")
        print(f"  vmax: {config.get('vmax')}")
    except KeyError as e:
        print(f"Error: Could not find config for {variable} - {year}")
        print(f"Available years for {variable}: {variables[variable]['years']}")
        print(f"Available configs: {list(variables[variable]['configs'].keys())}")
        return jsonify({'error': 'Configuration not found'}), 400

    # Handle aerial imagery
    if variable == 'aerial':
        print("Rendering aerial imagery template")
        return render_template_string("""
            <div class="bg-slate-800 p-4 rounded-md">
                <p class="mb-2 text-white">{{ title }} - {{ year }}</p>
                <div class="flex items-center gap-2 mb-2">
                    <div class="w-4 h-4 bg-red-500"></div>
                    <span class="text-white text-sm">Red Band (0-255)</span>
                </div>
                <div class="flex items-center gap-2 mb-2">
                    <div class="w-4 h-4 bg-green-500"></div>
                    <span class="text-white text-sm">Green Band (0-255)</span>
                </div>
                <div class="flex items-center gap-2">
                    <div class="w-4 h-4 bg-blue-500"></div>
                    <span class="text-white text-sm">Blue Band (0-255)</span>
                </div>
            </div>
        """, title=title, year=year)
    
    # Handle vegetation types
    elif variable == 'vegetation_types':
        print("Rendering vegetation types template")
        return render_template_string("""
            <div class="bg-slate-800 p-4 rounded-md">
                <p class="mb-4 text-white">{{ title }}</p>
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
        """, title=title)
    
    # Handle landcover
    elif variable == 'landcover':
        print("Rendering landcover template")
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
                <p class="mb-2 text-white">{{ title }}</p>
                <div class="space-y-2">
                    {% for item in legend_items %}
                    <div class="flex items-center gap-2">
                        <div class="w-4 h-4 border border-gray-600" style="background-color: {{ item.color }}"></div>
                        <span class="text-white text-sm">{{ item.label }}</span>
                    </div>
                    {% endfor %}
                </div>
            </div>
        """, title=title, legend_items=legend_items)
    
    # Handle continuous variables (bs, pv, ndvi, lai, gpp, wcf)
    else:
        print("Rendering continuous variable template")
        vmin, vmax = config['vmin'], config['vmax']
        cmap = config['cmap']
        
        # Check if this is a trend year
        is_trend = 'trend' in year.lower()
        print(f"Is trend year: {is_trend}")
        print(f"Year string: {year}")
        
        # Define color gradients for different cmaps
        cmap_gradients = {
            'BrBG': '#543005, #8C510A, #F6E8C3, #C7EAE5, #003C30',
            'BrBG_r': '#003C30, #C7EAE5, #F6E8C3, #8C510A, #543005',
            'RdBu': '#053061, #92C5DE, #F7F7F7, #F4A582, #67001F',
            'RdBu_r': '#67001F, #F4A582, #F7F7F7, #92C5DE, #053061'
        }
        
        gradient = cmap_gradients.get(cmap, '#000000, #FFFFFF')
        print(f"Selected colormap: {cmap}")
        print(f"Gradient colors: {gradient}")
        
        # Add units based on variable type
        units = {
            'bs': '%',
            'pv': '%',
            'ndvi': '',
            'lai': '',
            'gpp': 'gC/m²/d',
            'wcf': '%'
        }
        
        unit = units.get(variable, '')
        value_format = '{:g}' + unit  # Remove trailing zeros
        
        print(f"Variable unit: {unit}")
        print(f"vmin: {vmin} {unit}")
        print(f"vmax: {vmax} {unit}")
        
        return render_template_string("""
            <div class="bg-slate-800 p-4 rounded-md">
                <p class="mb-2 text-white">{{ title }}</p>
                {% if is_trend %}
                <p class="mb-4 text-sm text-slate-400">Trend per year (2004-2023)</p>
                {% endif %}
                <div class="w-full h-6 mb-2" style="background: linear-gradient(to right, {{ gradient }});"></div>
                <div class="flex justify-between">
                    <span class="text-white text-sm">{{ vmin_formatted }}</span>
                    <span class="text-white text-sm">{{ vmax_formatted }}</span>
                </div>
            </div>
        """, 
        title=title,
        is_trend=is_trend,
        gradient=gradient,
        vmin_formatted=value_format.format(vmin),
        vmax_formatted=value_format.format(vmax)
        )
        


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

