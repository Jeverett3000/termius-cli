# -*- coding: utf-8 -*-
"""Module with SecureCRT parser."""
from os.path import expanduser


class SecureCRTConfigParser(object):
    """SecureCRT xml parser."""

    meta_sessions = ['Default']

    def __init__(self, xml):
        """Construct parser instance."""
        self.xml = xml
        self.tree = {}

    def parse_hosts(self):
        """Parse SecureCRT Sessions."""
        sessions = list(self.get_element_by_name(list(self.xml), 'Sessions'))

        self.parse_sessions(sessions, self.tree)

        return self.tree

    def parse_sessions(self, sessions, parent_node):
        """Parse SecureCRT sessions."""
        for session in sessions:
            if session.get('name') not in self.meta_sessions:
                if self.is_session_group(session):
                    parent_node[session.get('name')] = {'__group': True}
                    self.parse_sessions(
                        list(session),
                        parent_node[session.get('name')]
                    )

                elif host := self.make_host(session):
                    parent_node[host['label']] = host

    def is_session_group(self, session):
        """Check node element type."""
        return self.get_element_by_name(list(session), 'Hostname') is None

    def parse_identity(self):
        """Parse SecureCRT SSH2 raw key."""
        identity = self.get_element_by_name(list(self.xml), 'SSH2')
        if identity is None:
            return None

        identity_filename = self.get_element_by_name(
            list(identity),
            'Identity Filename V2'
        )

        if not self.check_attribute(identity_filename):
            return None

        path = identity_filename.text.split('/')
        public_key_name = path[-1].split('::')[0]
        private_key_name = public_key_name.split('.')[0]

        if path[0].startswith('$'):
            path.pop(0)
            path.insert(0, expanduser("~"))

        path[-1] = public_key_name
        public_key_path = '/'.join(path)
        path[-1] = private_key_name
        private_key_path = '/'.join(path)

        return private_key_path, public_key_path

    def make_host(self, session):
        """Adapt SecureCRT Session to Termius host."""
        session_attrs = list(session)

        hostname = self.get_element_by_name(session_attrs, 'Hostname')
        port = self.get_element_by_name(session_attrs, '[SSH2] Port')
        username = self.get_element_by_name(session_attrs, 'Username')

        return (
            {
                'label': session.get('name'),
                'hostname': hostname.text,
                'port': port.text if self.check_attribute(port) else '22',
                'username': username.text
                if self.check_attribute(username)
                else None,
            }
            if self.check_attribute(hostname)
            else None
        )

    def check_attribute(self, attr):
        """Check an attribute."""
        return attr is not None and attr.text

    def get_element_by_name(self, elements, name):
        """Get SecureCRT config block."""
        return next(
            (element for element in elements if element.get('name') == name), None
        )
