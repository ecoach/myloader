from django.core.urlresolvers import reverse

def steps_nav(user, selected):
    
    all_steps = [
            #'text'         
            #   'styling_class(es)',    
            #       'links_to'
            #           'permission_required'
            #               'selected'
            ['1. Upload File', 
                '',  
                    reverse('myloader:file_upload'),
                        'staff',
                            'file_upload',

            ],
            ['2. Review File', 
                '',  
                    reverse('myloader:file_review'),
                        'staff',
                            'file_review',
            ],
            ['3. Digest Data', 
                '',  
                    reverse('myloader:data_digest'),
                        'staff',
                            'data_digest',
            ],
            ['4. Commit', 
                '',  
                    reverse('myloader:mts_load'),
                        'staff',
                            'mts_load',
            ],
            ['5. Archive', 
                '',  
                    reverse('myloader:archive'),
                        'staff',
                            'archive',
            ],
            ['Help', 
                '',  
                    reverse('myloader:help'),
                        'staff',
                            'help',
            ],
        ]

    steps_nav = []
    for nn in all_steps:
        # style the selected option
        if nn[4] == selected:
            nn[1] = 'current'
        # permission?
        if nn[3] == 'any':
            steps_nav.append(nn)
        elif nn[3] == 'staff' and user.is_staff:
            steps_nav.append(nn)

    return steps_nav

