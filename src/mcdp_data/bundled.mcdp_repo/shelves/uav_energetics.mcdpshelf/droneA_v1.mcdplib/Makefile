
all: solve plot

clean:
	rm -rf out/ _cached

solve:
	mcdp-solve --out=out/solve1 --plot --imp -d . Drone "<0s, 0kg, 0W>"
	#mcdp-solve --out=out/drone1/sb -d models/drone1 drone "<1 hour, 0kg>"


plot:
	mcdp-plot --out=out -d . Actuation
	mcdp-plot --out=out -d . Drone

