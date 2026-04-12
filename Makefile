run_app:
	python3 app.py & echo $$! > app.pid
	sleep 30

	wget -r http://127.0.0.1:8050/LOOP-H2/
	wget -r http://127.0.0.1:8050/LOOP-H2/_dash-layout 
	wget -r http://127.0.0.1:8050/LOOP-H2/_dash-dependencies

	wget -r http://127.0.0.1:8050/LOOP-H2/_dash-component-suites/dash/dcc/async-graph.js
	wget -r http://127.0.0.1:8050/LOOP-H2/_dash-component-suites/dash/dcc/async-highlight.js
	wget -r http://127.0.0.1:8050/LOOP-H2/_dash-component-suites/dash/dcc/async-markdown.js
	wget -r http://127.0.0.1:8050/LOOP-H2/_dash-component-suites/dash/dcc/async-datepicker.js

	wget -r http://127.0.0.1:8050/LOOP-H2/_dash-component-suites/dash/dash_table/async-table.js
	wget -r http://127.0.0.1:8050/LOOP-H2/_dash-component-suites/dash/dash_table/async-highlight.js

	wget -r http://127.0.0.1:8050/LOOP-H2/_dash-component-suites/plotly/package_data/plotly.min.js

	mv 127.0.0.1:8050/LOOP-H2 pages_files
	
	# Append .json to the API endpoints and disable backend-only Dash functions
	find pages_files -type f -exec sed -i.bak 's|_dash-layout|_dash-layout.json|g' {} \;
	find pages_files -type f -exec sed -i.bak 's|_dash-dependencies|_dash-dependencies.json|g' {} \;
	find pages_files -type f -exec sed -i.bak 's|_reload-hash|_reload-hash-disabled|g' {} \;
	find pages_files -type f -exec sed -i.bak 's|_dash-update-component|_dash-update-component-disabled|g' {} \;

	mv pages_files/_dash-layout pages_files/_dash-layout.json
	mv pages_files/_dash-dependencies pages_files/_dash-dependencies.json
	
	# Fallback copy for any unlinked local assets (like standalone images)
	cp -r assets/* pages_files/assets/ || true

	kill -9 `cat app.pid` || true
	rm app.pid

clean_dirs:
	rm -rf 127.0.0.1:8050/
	rm -rf pages_files/
	rm -rf joblib