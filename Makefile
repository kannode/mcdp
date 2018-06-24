
out=out/comptests

package=mcdp_tests

libraries=src/mcdp_data/bundled.mcdp_repo/shelves

all:
	echo "Instructions:"

serve-local:
	DISABLE_CONTRACTS=1 PYRAMID_RELOAD_TEMPLATES=1 pserve --reload ../mcdp-user-db/config/local.ini

include Makefile.tests

THESE_FIRST=mcdp_tests-composing1

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

include docker/Makefile.docker
