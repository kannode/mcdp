
out=out/comptests

package=mcdp_tests

libraries=src/mcdp_data/bundled.mcdp_repo/shelves

all:
	echo "Instructions:"

serve-local:
	DISABLE_CONTRACTS=1 PYRAMID_RELOAD_TEMPLATES=1 pserve --reload ../mcdp-user-db/config/local.ini


include Makefile.tests
include Makefile.coverage


clean:
	rm -rf $(out) out/opt_basic_*


readme-commands:
	mcdp-solve -d $(libraries)/examples/example-battery.mcdplib battery "<1 hour, 0.1 kg, 1 W>"
	mcdp-solve -d $(libraries)/examples/example-battery.mcdplib battery "<1 hour, 1.0 kg, 1 W>"

check-unicode-encoding-line:
	grep 'coding: utf-8' -r --include '*.py' -L  src/

serve-continuously:
	./misc/serve_continuously.sh

main_modules=mcdp\
mcdp_cli\
mcdp_comp_tests\
mcdp_data\
mcdp_depgraph\
mcdp_docs\
mcdp_docs_tests\
mcdp_dp\
mcdp_dp_tests\
mcdp_figures\
mcdp_figures_tests\
mcdp_hdb\
mcdp_hdb_mcdp\
mcdp_hdb_mcdp_tests\
mcdp_hdb_tests\
mcdp_ipython_utils\
mcdp_lang\
mcdp_lang_tests\
mcdp_lang_utils\
mcdp_library\
mcdp_library_tests\
mcdp_maps\
mcdp_opt\
mcdp_opt_tests\
mcdp_posets\
mcdp_posets_tests\
mcdp_repo\
mcdp_report\
mcdp_report_ndp_tests\
mcdp_repo_tests\
mcdp_shelf\
mcdp_shelf_tests\
mcdp_tests\
mcdp_user_db\
mcdp_utils_gitrepo\
mcdp_utils_indexing\
mcdp_utils_misc\
mcdp_utils_xml\
mcdp_web\
mcdp_web_tests\
mocdp

test-dependencies.deps:
	cd src && sfood $(main_modules) > $@

%.dot: %.deps
	sfood-graph < $< > $@

%.pdf: %.dot
	dot -Tpdf -o$@ $<

css:
	$(MAKE) -C src/mcdp_web/static/css/

python-module-stats:
	./misc/python_environment.py \
		compmake\
		contracts\
		decent_logs\
		quickapp\
		conf_tools\
		comptests\
		ruamel.yaml\
		ruamel.ordereddict\
		geometry\
		bs4\
		cv2\
		matplotlib\
		networkx\
		Pillow\
		qtfaststart\
		selenium

	piprot

include docker/Makefile.docker

include Makefile.utils
