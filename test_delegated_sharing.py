##
## test_delegated_sharing.py - Some tests for delegated sharing (CS1620/2660)
##

import unittest
import string

import support.crypto as crypto
import support.util as util

from support.dataserver import dataserver, memloc
from support.keyserver import keyserver

# Import your client
#from client import create_user, authenticate_user

# Use this in place of the above line to test using the reference client
from dropbox_client_reference import create_user, authenticate_user


class DelegatedSharingTests(unittest.TestCase):
    def setUp(self):
        """
        This function is automatically called before every test is run. It
        clears the dataserver and keyserver to a clean state for each test case.
        """
        dataserver.Clear()
        keyserver.Clear()

    def test_chain(self):
        """Test sharing chain 1 -> 2 -> 3"""

        create_user("usr1", "pswd")
        create_user("usr2", "pswd")
        create_user("usr3", "pswd")
        
        u1 = authenticate_user("usr1", "pswd")
        u2 = authenticate_user("usr2", "pswd")
        u3 = authenticate_user("usr3", "pswd")

        u1.upload_file("shared_file", b'shared data')
        u1.share_file("shared_file", "usr2")
        u2.receive_file("shared_file", "usr1")
        u2.share_file("shared_file", "usr3")
        u3.receive_file("shared_file", "usr2")
        
        u1_file = u1.download_file("shared_file")
        u2_file = u2.download_file("shared_file")
        u3_file = u3.download_file("shared_file")

        self.assertEqual(u1_file, b'shared data')
        self.assertEqual(u2_file, b'shared data')
        self.assertEqual(u3_file, b'shared data')
    
    def test_chain_receive(self):
        """
        Test sharing chain 1 -> 2 -> 3
        Check that 2 needs to receive file before sharing with 3
        """

        create_user("usr1", "pswd")
        create_user("usr2", "pswd")
        create_user("usr3", "pswd")
        
        u1 = authenticate_user("usr1", "pswd")
        u2 = authenticate_user("usr2", "pswd")
        u3 = authenticate_user("usr3", "pswd")

        u1.upload_file("shared_file", b'shared data')
        u1.share_file("shared_file", "usr2")
        
        with self.assertRaises(util.DropboxError):
            u2.share_file("shared_file", "usr3")
    
    def test_chain_revoke(self):
        """
        Test sharing chain 1 -> 2 -> 3
        Both 2 & 3 lose access after 1 revokes file from 2
        """
        
        create_user("usr1", "pswd")
        create_user("usr2", "pswd")
        create_user("usr3", "pswd")
        
        u1 = authenticate_user("usr1", "pswd")
        u2 = authenticate_user("usr2", "pswd")
        u3 = authenticate_user("usr3", "pswd")

        u1.upload_file("shared_file", b'shared data')
        u1.share_file("shared_file", "usr2")
        u2.receive_file("shared_file", "usr1")
        u2.share_file("shared_file", "usr3")
        u3.receive_file("shared_file", "usr2")
        
        u1.revoke_file("shared_file", "usr2")
        
        with self.assertRaises(util.DropboxError):
            u2.download_file("shared_file")
        
        with self.assertRaises(util.DropboxError):
            u3.download_file("shared_file")
        
    def test_tree_DFS(self):
        """
        Test sharing files DFS style
        1 -> 2 -> 4
               -> 5
          -> 3 -> 6
               -> 7
        """
        users = []
        for i in range(7):
            create_user(f"usr{i+1}", "pswd")
            u = authenticate_user(f"usr{i+1}", "pswd")
            users.append(u)
        
        u1, u2, u3, u4, u5, u6, u7 = users
        
        u1.upload_file("shared_file", b'shared data')
        
        u1.share_file("shared_file", "usr2")
        u2.receive_file("shared_file", "usr1")
        u2.share_file("shared_file", "usr4")
        u4.receive_file("shared_file", "usr2")
        u2.share_file("shared_file", "usr5")
        u5.receive_file("shared_file", "usr2")
        u1.share_file("shared_file", "usr3")
        u3.receive_file("shared_file", "usr1")
        u3.share_file("shared_file", "usr6")
        u6.receive_file("shared_file", "usr3")
        u3.share_file("shared_file", "usr7")
        u7.receive_file("shared_file", "usr3")
        
        for user in users:
            file = user.download_file("shared_file")
            self.assertEqual(file, b'shared data')
    
    def test_tree_BFS(self):
        """
        Test sharing files BFS style
        1 -> 2 -> 4
               -> 5
          -> 3 -> 6
               -> 7
        """
        users = []
        for i in range(7):
            create_user(f"usr{i+1}", "pswd")
            u = authenticate_user(f"usr{i+1}", "pswd")
            users.append(u)
        
        u1, u2, u3, u4, u5, u6, u7 = users
        
        u1.upload_file("shared_file", b'shared data')
        
        u1.share_file("shared_file", "usr2")
        u1.share_file("shared_file", "usr3")
        u2.receive_file("shared_file", "usr1")
        u3.receive_file("shared_file", "usr1")
        u2.share_file("shared_file", "usr4")
        u2.share_file("shared_file", "usr5")
        u3.share_file("shared_file", "usr6")
        u3.share_file("shared_file", "usr7")
        u4.receive_file("shared_file", "usr2")
        u5.receive_file("shared_file", "usr2")
        u6.receive_file("shared_file", "usr3")
        u7.receive_file("shared_file", "usr3")
        
        for user in users:
            file = user.download_file("shared_file")
            self.assertEqual(file, b'shared data')
    
    def test_tree_revoke(self):
        users = []
        for i in range(7):
            create_user(f"usr{i+1}", "pswd")
            u = authenticate_user(f"usr{i+1}", "pswd")
            users.append(u)
        
        u1, u2, u3, u4, u5, u6, u7 = users
        
        u1.upload_file("shared_file", b'shared data')
        
        u1.share_file("shared_file", "usr2")
        u1.share_file("shared_file", "usr3")
        u2.receive_file("shared_file", "usr1")
        u3.receive_file("shared_file", "usr1")
        u2.share_file("shared_file", "usr4")
        u2.share_file("shared_file", "usr5")
        u3.share_file("shared_file", "usr6")
        u3.share_file("shared_file", "usr7")
        u4.receive_file("shared_file", "usr2")
        u5.receive_file("shared_file", "usr2")
        u6.receive_file("shared_file", "usr3")
        u7.receive_file("shared_file", "usr3")
        
        u1.revoke_file("shared_file", "usr2")
        
        with self.assertRaises(util.DropboxError):
            u2.download_file("shared_file")
            
        with self.assertRaises(util.DropboxError):
            u4.download_file("shared_file")
            
        with self.assertRaises(util.DropboxError):
            u5.download_file("shared_file")
        
        file = u3.download_file("shared_file")
        self.assertEqual(file, b'shared data')
        file = u6.download_file("shared_file")
        self.assertEqual(file, b'shared data')
        file = u7.download_file("shared_file")
        self.assertEqual(file, b'shared data')


# Start the REPL if this file is launched as the main program
if __name__ == '__main__':
    util.start_repl(locals())