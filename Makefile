run_app:
	python3 app.py & echo $$! > app.pid
	sleep 30

	wget -r http://127.0.0.1:8050/
	wget -r http://127.0.0.1:8050/_dash-layout 
	wget -r http://127.0.0.1:8050/_dash-dependencies

	wget -r http://127.0.0.1:8050/_dash-component-suites/dash/dcc/async-graph.js
	wget -r http://127.0.0.1:8050/_dash-component-suites/dash/dcc/async-highlight.js
	wget -r http://127.0.0.1:8050/_dash-component-suites/dash/dcc/async-markdown.js
	wget -r http://127.0.0.1:8050/_dash-component-suites/dash/dcc/async-datepicker.js

	wget -r http://127.0.0.1:8050/_dash-component-suites/dash/dash_table/async-table.js
	wget -r http://127.0.0.1:8050/_dash-component-suites/dash/dash_table/async-highlight.js

	wget -r http://127.0.0.1:8050/_dash-component-suites/plotly/package_data/plotly.min.js

	mv 127.0.0.1:8050 pages_files
	ls -a pages_files
	ls -a pages_files/assets

	find pages_files -type f -exec sed -i.bak 's|_dash-component-suites|LOOP-H2/_dash-component-suites|g' {} \;
	find pages_files -type f -exec sed -i.bak 's|_dash-layout|LOOP-H2/_dash-layout.json|g' {} \;
	find pages_files -type f -exec sed -i.bak 's|_dash-dependencies|LOOP-H2/_dash-dependencies.json|g' {} \;
	find pages_files -type f -exec sed -i.bak 's|_reload-hash|LOOP-H2/_reload-hash|g' {} \;
	find pages_files -type f -exec sed -i.bak 's|_dash-update-component|LOOP-H2/_dash-update-component|g' {} \;
	find pages_files -type f -exec sed -i.bak 's|assets|LOOP-H2/assets|g' {} \;

	mv pages_files/_dash-layout pages_files/_dash-layout.json
	mv pages_files/_dash-dependencies pages_files/_dash-dependencies.json
	mv assets/* pages_files/assets/

	kill -9 `cat app.pid` || true
	rm app.pid

clean_dirs:
	ls
	rm -rf 127.0.0.1:8050/
	rm -rf pages_files/
	rm -rf joblib