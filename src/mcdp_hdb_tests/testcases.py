from copy import deepcopy

from contracts import contract

from mcdp_hdb import DiskMap
from mcdp_hdb import SchemaBase, Schema, SchemaString
from mcdp_hdb import ViewManager
from mcdp_hdb import assert_data_events_consistent
from mcdp_hdb import event_interpret_


class DataTestCase(object):
    

    @contract(schema=SchemaBase, events=list, disk_map=DiskMap)
    def __init__(self, schema, data1, events, data2, disk_map):   
        schema.validate(data1)
        schema.validate(data2) 
        assert_data_events_consistent(schema, data1, events, data2)
        self.data1 = data1
        self.events = events
        self.data2 = data2
        self.disk_map = disk_map
        self.schema = schema
        
    def get_data1(self):
        ''' Returns a copy of data1 (safe to modify) '''
        return deepcopy(self.data1)
    
    def get_data2(self):
        ''' Returns a copy of data2 (safe to modify) '''
        return deepcopy(self.data2)
    
    @contract(returns=SchemaBase)
    def get_schema(self):
        ''' returns the schema '''
        return self.schema

    @contract(returns=list)
    def get_events(self):
        return deepcopy(self.events)
    
    @contract(returns=DiskMap)
    def get_disk_map(self):
        return self.disk_map
    
    def enumerate_data_diff(self):
        ''' 
            Enumerates the transitions. Use as:
            for d1, data_event, d2 in enumerate_data_diff():
        ''' 
        data_i = self.get_data1()
        view_manager = ViewManager(self.schema)
        for e in self.events:
            current = deepcopy(data_i)
            view = view_manager.view(data_i)
            event_interpret_(view, e)
            yield current, e, data_i
    
@contract(returns='dict(str:isinstance(DataTestCase))')    
def testcases_SimpleUserDB():
    
    db_schema = Schema()
    schema_user = Schema()
    schema_user.string('name')
    schema_user.string('email', can_be_none=True)
    schema_user.list('groups', SchemaString())
    db_schema.hash('users', schema_user)
    
    db0 = {
        'users': { 
            'andrea': {
                'name': 'Andrea', 
                'email': 'info@co-design.science',
                'groups': ['group:admin', 'group:FDM'],
            },
            'pinco': {
                'name': 'Pinco Pallo', 
                'email': None,
                'groups': ['group:FDM'],
            },
        }
    }

    db_schema.validate(db0)
    db = deepcopy(db0)
    events = []
    viewmanager = ViewManager(db_schema) 
    view = viewmanager.view(db)
    def notify_callback(event):
        #logger.debug('\n' + yaml_dump(event))
        events.append(event)
    view._notify_callback = notify_callback

    users = view.users
    u = users['andrea'] 
    u.name = 'not Andrea'
    u.email = None    
    users['another'] = {'name': 'Another', 'email': 'another@email.com', 'groups':['group:extra']}
    del users['another']
    users.rename('pinco', 'pallo')
#     db_replay = deepcopy(db0)
#     replay_events(viewmanager, db_replay, events) 
#     assert_data_equal(db_schema, db_replay, db)
    
    assert_data_events_consistent(db_schema, db0, events, db)
    
    
    disk_map_with_hint = DiskMap(db_schema)
    disk_map_with_hint.hint_directory(db_schema['users'], pattern='%.user')
    
    disk_map_files_are_yaml= DiskMap(db_schema)
    disk_map_files_are_yaml.hint_directory(db_schema['users'], pattern='%.yaml')
    disk_map_files_are_yaml.hint_file_yaml(db_schema['users'].prototype)
    disk_maps= {}
    disk_maps['vanilla'] = DiskMap(db_schema)
    disk_maps['with_hint'] = disk_map_with_hint
    disk_maps['files_are_yaml'] = disk_map_files_are_yaml
    
    res = {}
    for k in disk_maps:
        dm = disk_maps[k]
        res[k] = DataTestCase(db_schema, db0, events, db, dm)
    return res

