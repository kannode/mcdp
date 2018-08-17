

Idea: 1-1 map between the text and the graphical representation (*not* the interpreted model).



``
mcdp {
    provides a [unit]; 


}
```


```
provides a [unit];
```


```
a+b
```



```
a = instance `library.x
```


maneuver 1  yes/no
maneuver 2  slow/fast/ultra


maneuver 3 yes/no



features: {
    maneuver1: Bool,
    maneuver2: poset{ slow <= fast <= ultra},
}

features2 {
    maneuver3: Bool,
}



F - [base model] -- 
