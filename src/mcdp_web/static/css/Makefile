
others=*.less

d=compiled



versions=$(wildcard v_*.less)
targets0=$(versions:.less=.css)
targets=$(foreach a, $(targets0), $(d)/$(a))



all: $(targets)


compiled/%.css: %.less $(others)
	lessc --verbose $< $@.tmp
	@cat banner.txt > $@
	@cat $@.tmp >> $@
	@rm $@.tmp
	@cat banner.txt >> $@
	-stylelint $@
