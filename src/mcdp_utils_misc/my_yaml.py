from contracts import raise_wrapped, indent

__all__ = [
    'yaml_load', 
    'yaml_dump',
]

if True:
    from ruamel import yaml  # @UnresolvedImport
    # XXX: does not represent None as null, rather as '...\n'
    def yaml_load(s):
        if s.startswith('...'):
            return None
        return yaml.load(s, Loader=yaml.RoundTripLoader)
    
    def yaml_dump(s):
        return yaml.dump(s, Dumper=yaml.RoundTripDumper)

    def yaml_dump_pretty(ob):
        return yaml.dump(ob, Dumper=yaml.RoundTripDumper)

else:
    import yaml  # @Reimport
    def yaml_load(s):
        return yaml.load(s)
    
    def yaml_dump(s):
        return yaml.dump(s)
    
    yaml_dump_pretty = yaml_dump


class CouldNotReadYAML(Exception):
    pass

import os

def read_and_interpret_yaml_file(filename, f, plain_yaml=False):
    """
        f is a function that takes

            f(filename, data)

        f can raise ValueError """
    if not os.path.exists(filename):
        msg = "file does not exist: %s" % filename
        raise CouldNotReadYAML(msg)
    try:
        from ruamel.yaml.error import YAMLError
        contents= open(filename).read()
        try:
            # if plain_yaml:
            #     data = yaml_load_plain(contents)
            # else:
            data = yaml_load(contents)
        except YAMLError as e:
            msg = 'Invalid YAML content:'
            raise_wrapped(CouldNotReadYAML, e, msg, compact=True)
            raise
        except TypeError as e:
            msg = 'Invalid YAML content; this usually happens '
            msg += 'when you change the definition of a class.'
            raise_wrapped(CouldNotReadYAML, e, msg, compact=True)
            raise
        try:
            return f(filename, data)
        except ValueError as e:
            msg = 'Could not interpret.'
            raise_wrapped(CouldNotReadYAML, e, msg)

    except CouldNotReadYAML as e:
        msg = 'Could not interpret the contents of the file using %s()\n' % f.__name__
        msg += '   %s\n' % filename
        # msg += 'Contents:\n' + indent(contents[:300], ' > ')
        raise_wrapped(CouldNotReadYAML, e, msg, compact=True)

