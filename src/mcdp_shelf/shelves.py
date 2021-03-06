from contracts import contract

__all__ = [
    'Shelf',
]

class Shelf(object):
    ''' 
        A shelf has:
        - a set of libraries
        - a set of access control permissions 
        - a list of dependencies
        - a short description (one line, pure text)
        - a long description (markdown)
        - a list of authors

        - a default directory for creating a new library
    ''' 
    
    @contract(returns='list(str)')
    def get_dependencies(self):
        return list(self.info.dependencies)

    @contract(returns='list(str)')
    def get_authors(self):
        return list(self.info.authors)

    @contract(returns='str|None')
    def get_desc_short(self):
        return self.info.desc_short

    @contract(returns='str|None')
    def get_desc_long(self):
        return self.info.desc_long 
# 
#         self.libraries = find_libraries(self.dirname)
#     def update_libraries(self):

# 
# def shelf_from_directory(dirname):
#     ''' Dirname should end in shelf_extension '''
#     try:
#         return shelf_from_directory_(dirname)
#     except ValueError as e:
#         msg = 'While reading shelf from %s:' % dirname
#         raise_wrapped(FormatException, e, msg, compact=True)
#         
# def shelf_from_directory_(dirname):
#     if not dirname.endswith(MCDPConstants.shelf_extension):
#         msg = 'Wrong name for shelf: %r' % dirname
#         raise ValueError(msg)
# 
#     fn = os.path.join(dirname, MCDPConstants.shelf_desc_file)
#     if not os.path.exists(fn):
#         msg = 'File %r does not exist.' % fn
#         raise ValueError(msg)
# 
#     u = read_file_encoded_as_utf8(fn)
#     try:
#         y = yaml_load(u)
#         acl = acl_from_yaml(y.pop('acl', MCDPConstants.default_acl))
#         dependencies = y.pop('dependencies', [])
#         desc_short = y.pop('desc_short', None)
#         desc_long = y.pop('desc_long', None)
#         authors = y.pop('authors', [])
#         expect_fields = ['acl','desc_short','desc_long','authors']
#         if y:
#             msg = 'Unknown fields %s; expected %s' % (list(y), expect_fields)
#             raise_desc(FormatException, msg, filename=fn, contents=u)
#     except:
#         msg = 'Cannot parse %s:\n%s' % (fn, indent_plus_invisibles(u))
#         logger.error(msg)
#         raise
# 
#     shelf = Shelf(acl=acl, dependencies=dependencies, desc_short=desc_short,
#                   desc_long=desc_long, libraries={}, authors=authors,
#                   dirname=dirname, write_to=dirname)
#     shelf.update_libraries()
#     return shelf

# 
# @contract(returns='dict(str:$Shelf)')
# def find_shelves(dirname):
#     ''' Find shelves underneath the directory. '''
#     ds = locate_files(dirname, "*.%s" % MCDPConstants.shelf_extension,
#                       followlinks=True,
#                       include_directories=True,
#                       include_files=False)
#     res = {}
#     for d in ds:
#         name = os.path.splitext(os.path.basename(d))[0]
#         res[name] = shelf_from_directory(d)
#     return res
