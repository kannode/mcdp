
out=out/comptests

package=mcdp_tests

libraries=src/mcdp_data/bundled.mcdp_repo/shelves

all:
	echo "Instructions:"

serve-local:
	DISABLE_CONTRACTS=1 PYRAMID_RELOAD_TEMPLATES=1 pserve --reload ../mcdp-user-db/config/local.ini

prepare_tests:
	mkdir -p $(out)

	DISABLE_CONTRACTS=1 $(MAKE) -C $(libraries)/unittests.mcdpshelf/basic.mcdplib/generated_dps/ clean all

comptests: prepare_tests
	comptests -o $(out) --contracts --nonose --console $(package)

comptests-nocontracts: prepare_tests
	comptests -o $(out) --nonose --console $(package)

comptests-run: prepare_tests
	comptests -o $(out) --contracts --nonose $(package)

comptests-run-nocontracts: prepare_tests
	comptests -o $(out) --nonose $(package)
	compmake $(out) -c "ls failed"

comptests-run-nocontracts-console: prepare_tests
	comptests -o $(out) --nonose $(package) --console

comptests-run-parallel: prepare_tests
	comptests -o $(out) --contracts --nonose -c "rparmake" $(package)

comptests-run-parallel-nocontracts: prepare_tests
	DISABLE_CONTRACTS=1 \
	MCDP_TEST_LIBRARIES_EXCLUDE="mcdp_theory,droneD_complete_templates" \
		comptests -o $(out) --nonose -c "rparmake" $(package)

circle-1-of-4:
	CIRCLE_NODE_INDEX=0 CIRCLE_NODE_TOTAL=4 $(MAKE) circle


circle-3-of-4:
	CIRCLE_NODE_INDEX=2 CIRCLE_NODE_TOTAL=4 $(MAKE) circle


circle: prepare_tests
	echo Make: $(CIRCLE_NODE_INDEX) " of " $(CIRCLE_NODE_TOTAL)
	DISABLE_CONTRACTS=1 \
	# MCDP_TEST_LIBRARIES_EXCLUDE="mcdp_theory,droneD_complete_templates,manual" \
	# 	comptests -o $(out) --nonose -c "rparmake n=2" $(package)
	# MCDP_TEST_LIBRARIES_EXCLUDE="mcdp_theory,droneD_complete_templates" \
	# 	strace -o $(CIRCLE_NODE_INDEX).trace -ff comptests -o $(out) --nonose -c "rmake" $(package)
	MCDP_TEST_LIBRARIES_EXCLUDE="mcdp_theory,droneD_complete_templates" \
		comptests -o $(out) --nonose -c "rmake" $(package)
	# ./misc/t ls failed
	# ./misc/t parmake

comptests-run-parallel-nocontracts-onlysetup: prepare_tests
	DISABLE_CONTRACTS=1 comptests -o $(out) --nonose -c "parmake dynamic and ready; parmake dynamic and ready; parmake dynamic and ready" $(package)

comptests-run-parallel-nocontracts-cov: prepare_tests
	DISABLE_CONTRACTS=1 comptests -o $(out) --coverage --nonose -c "rparmake" $(package)

comptests-run-parallel-nocontracts-prof: prepare_tests
	DISABLE_CONTRACTS=1 comptests -o $(out) --profile --nonose -c "make; rparmake" $(package)


docoverage-single: prepare_tests
	# note you need "rmake" otherwise it will not be captured
	rm -rf ouf_coverage .coverage
	-DISABLE_CONTRACTS=1 comptests -o $(out) --nonose -c "exit" $(package)
	-DISABLE_CONTRACTS=1 coverage2 run `which compmake` $(out) -c "rmake"
	coverage html -d out_coverage --include '*src/mcdp*'

docoverage-parallel: prepare_tests
	# note you need "rmake" otherwise it will not be captured
	rm -rf ouf_coverage .coverage .coverage.*
	-DISABLE_CONTRACTS=1 MCDP_TEST_LIBRARIES_EXCLUDE="mcdp_theory" comptests -o $(out) --nonose -c "exit" $(package)
	-DISABLE_CONTRACTS=1 coverage run --concurrency=multiprocessing  `which compmake` $(out) -c "rparmake"
	coverage combine
	$(MAKE) coverage-report
	$(MAKE) coverage-coveralls
	#coverage html -d out_coverage --include '*src/mcdp*'

coverage-report:
	coverage html -d out_coverage --include '*src/mcdp*'

coverage-coveralls:
	# without --nogit, coveralls does not find the source code
	COVERALLS_REPO_TOKEN=LDWrmw94YNEgp8YSpJ6ifSWb9aKfQt3wC coveralls --nogit --base_dir .

clean:
	rm -rf $(out) out/opt_basic_*
	#_cached


stats-locs:
	wc -l `find . -type f -name '*.py' | grep -v test`

stats-locs-tests:
	wc -l `find . -type f -name '*.py' | grep test`


# bump-upload:
# 	bumpversion patch
# 	git push --tags
# 	python setup.py sdist upload

bump-upload:
	bumpversion patch
	git push --tags
	git push --all
	rm -f dist/*
	python setup.py sdist
	twine upload dist/*

readme-commands:
	mcdp-solve -d $(libraries)/examples/example-battery.mcdplib battery "<1 hour, 0.1 kg, 1 W>"
	mcdp-solve -d $(libraries)/examples/example-battery.mcdplib battery "<1 hour, 1.0 kg, 1 W>"

check-unicode-encoding-line:
	grep 'coding: utf-8' -r --include '*.py' -L  src/

clean-branches:
	@echo First delete branches on Github.
	@echo Then run this command.
	@echo
	git fetch -p && git branch -vv | awk '/: gone]/{print $$1}' | xargs git branch -d


naked-prints:
	zsh -c "grep '^[[:space:]]*print ' src/**/*py 2>/dev/null  | grep -v gvgen | grep -v pyparsing_bundled | grep -v /libraries | grep -v XCP | grep -v node_modules | grep -v tests"


list-ignored:
	git status --ignored src | grep -v pyc | grep -v .DS_Store | grep -v out/ | grep -v .compmake_history.txt | grep -v _cached | grep -v .egg-info


big-files-in-git:
	git rev-list --objects --all | grep "$(git verify-pack -v .git/objects/pack/*.idx | sort -k 3 -n | tail -10 | awk '{print$1}')"

branches-to-merge:
	@echo  "\nThese branches need to be merged in the current branch:\n"
	@git branch -a --no-merged

show-unicode:
	cat src/mcdp_lang/*.py | python show_not_ascii.py

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

include Makefile.docker
