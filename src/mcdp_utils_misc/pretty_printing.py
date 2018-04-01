from contracts.utils import indent


def pretty_print_dict(d, MAX=None):
    lengths = [len(k) for k in d.keys()]
    if not lengths:
        return 'Empty.'
    klen = max(lengths)
    s = []
    for k, v in d.items():
        if isinstance(k, tuple):
            k = k.__repr__()
        k2 = k.rjust(klen)
        prefix = "%s: " % k2
        v_s = str(v)
        if MAX is not None:
            if len(v_s) > MAX:
                v_s = '[First %s chars] %s' % (MAX, v_s[:MAX])
        s.append(indent(v_s, '', prefix))
    return "\n".join(s)


def pretty_print_dict_newlines(d):
    lengths = [len(k) for k in d.keys()]
    if not lengths:
        return 'Empty.'

    s = ""
    for k, v in d.items():
        if isinstance(k, tuple):
            k = k.__repr__()
        if s:
            s += '\n\n'
        s += k
        s += '\n\n' + indent(str(v), '  ')
    return s
