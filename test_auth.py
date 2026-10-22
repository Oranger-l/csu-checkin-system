import unittest
from unittest.mock import Mock, patch
from auth import cas_login, LoginError, CAS_H5_SERVICE, CAS_LOGIN_URL


def response(url, text='', status=200, result=None, headers=None):
    return Mock(url=url, text=text, status_code=status, headers=headers or {},
                json=Mock(return_value=result))


class LoginFlowTests(unittest.TestCase):
    callback = "var uid = 'test-user'; var lzc = 'test-ticket';"
    result = {'code': '200', 'data': {'token': 'test-token', 'yhzh': 'test-user'}}

    def test_existing_sso_callback_does_not_submit_password(self):
        session = Mock(headers={})
        session.get.return_value = response(CAS_H5_SERVICE, self.callback)
        session.post.return_value = response(CAS_H5_SERVICE, result=self.result)
        result = cas_login('test-user', 'test-password', session)
        self.assertEqual(result[0], 'test-token')
        self.assertEqual(result[3], 'test-user')
        self.assertEqual(session.post.call_count, 1)
        self.assertTrue(session.post.call_args.args[0].endswith('/login-other'))
        self.assertNotIn('test-password', session.post.call_args.kwargs['data'])
        self.assertTrue(session.verify)

    @patch('auth.encrypt_cas_password', return_value='encrypted')
    def test_expired_sso_uses_normal_password_login(self, encrypt):
        session = Mock(headers={})
        session.get.side_effect = [
            response(CAS_LOGIN_URL, '<input id="pwdEncryptSalt" value="salt"><input name="execution" value="execution">'),
            response(CAS_H5_SERVICE, self.callback),
        ]
        session.post.side_effect = [
            response(CAS_LOGIN_URL, status=302, headers={'Location': CAS_H5_SERVICE + '?ticket=test'}),
            response(CAS_H5_SERVICE, result=self.result),
        ]
        self.assertEqual(cas_login('test-user', 'test-password', session)[0], 'test-token')
        encrypt.assert_called_once_with('test-password', 'salt')
        self.assertEqual(session.post.call_count, 2)

    def test_unexpected_redirect_does_not_submit_password(self):
        session = Mock(headers={})
        session.get.return_value = response('https://unexpected.example/?token=private', self.callback)
        with self.assertRaises(LoginError) as caught:
            cas_login('test-user', 'test-password', session)
        session.post.assert_not_called()
        self.assertNotIn('private', str(caught.exception))


if __name__ == '__main__':
    unittest.main()
