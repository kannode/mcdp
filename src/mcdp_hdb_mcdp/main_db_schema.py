# -*- coding: utf-8 -*-
from mcdp import MCDPConstants
from mcdp_hdb  import Schema, SchemaString, SchemaList,\
    SchemaHash,  DiskMap
from mcdp_hdb.memdataview_manager import ViewManager
from mcdp_library.specs_def import specs
from mcdp_user_db.user import UserInfo
from mcdp_user_db.userdb import UserDB


class DB():
    
    db = Schema()
    library = Schema()
    image = Schema()
    image_extensions = sorted(set(_.lower() for _ in MCDPConstants.exts_images))
    for ext in image_extensions:
        image.bytes(ext, can_be_none=True) # and can be none
    library.hash('images', image)
    library.hash('documents', SchemaString())
    
    with library.context_e('things') as things:
        for spec_name, spec in specs.items():  # @UnusedVariable
            thing = SchemaString()
            things.hash(spec_name, thing)

    shelf = Schema()
    with shelf.context_e('info') as shelf_info:
        shelf_info.string('desc_short',  can_be_none=True)
        shelf_info.string('desc_long',  can_be_none=True)
        shelf_info.list("authors", SchemaString())
        shelf_info.list("dependencies", SchemaString())
        acl_entry = SchemaList(SchemaString())
        shelf_info.list('acl', acl_entry)
    
    shelf.hash('libraries', library)
    shelves = SchemaHash(shelf)
    
    repo = Schema() 
    repo._add_child('shelves', shelves)

    user = Schema() 
    with user.context_e('info') as user_info:
        user_info.string('name')
        user_info.date('account_created', can_be_none=True)
        user_info.date('account_last_active',  can_be_none=True)
        user_info.string('website',  can_be_none=True)
        user_info.string('affiliation',  can_be_none=True)
        user_info.list('subscriptions', SchemaString())
        user_info.string('email', can_be_none=True)
        with user_info.list_e('authentication_ids') as auth_id:
            auth_id.string('provider')
            auth_id.string('id', can_be_none=True)
            auth_id.string('password',  can_be_none=True)
        user_info.list('groups', SchemaString())
    users = SchemaHash(user)
    
    user_db = Schema()
    user_db._add_child('users', users)
    db._add_child('user_db', user_db)
    
    dm = DiskMap()
    dm.hint_directory(shelves, pattern='%.mcdpshelf')
    dm.hint_directory(shelf, translations={'info':'mcdpshelf.yaml', 'libraries':None})
    dm.hint_file_yaml(shelf['info'])
    dm.hint_directory(shelf['libraries'], pattern='%.mcdplib')
    dm.hint_directory(users, pattern='%.mcdp_user') 
    dm.hint_directory(user, translations={'info':'user.yaml'})
    dm.hint_file_yaml(user['info'])
    dm.hint_directory(user_db,translations={'users':None})
                      
    dm.hint_directory(library, translations={'images': None, 'documents': None, 'things': None})
    dm.hint_extensions(library['images'], image_extensions)
    dm.hint_directory(library['documents'], pattern='%.md')
    spec_translations = dict((k,None) for k in list(specs))
    dm.hint_directory(things, translations=spec_translations)
    
    for spec_name, spec in specs.items():  # @UnusedVariable
        dm.hint_directory(things[spec_name], pattern='%.' + spec.extension)

    view_manager = ViewManager(db)
    view_manager.set_view_class(user_info, UserInfo)
    view_manager.set_view_class(user_db, UserDB)
    
#     user2 = Schema()
    # info/ 
    #     public/      # Things that everybody can see
    #        name
    #            full:
    #            nick:             
    #        links:
    #            website:
    #            twitter:
    #            github: 
    #            coinbase
    #        affiliation:
    #        __acl__:
    #            allow special:self write 
    #            allow system:authenticated read
    #     private/     # Things that the user can change 
    #        __acl__:
    #            allow self write 
    #            allow self read
    #        email
    #            __acl__
    #                allow-if:../preferences/email_is_public system:authenticated read  
    #        preferences:
    #            email_is_public : bool 
    #     system/ 
    #        groups
    #        subscriptions []: 
    #            repo: <repo_name>
    #            shelf: <shelf_name>
    #            version: <version> or 'latest'
    #        authentication_ids[]:
    #        verified_emails/
    #            <email>: <date>
    #        authentication_history []:
    #            installation: <system>
    #            date: <date>
    #            method: <date>
    #            where: <where in the world>
    #        activity/
    #            likes: []    
    # 