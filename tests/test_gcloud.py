# from unittest.mock import patch, MagicMock, mock_open
# import termux_dev_setup.gcloud as g

# def test_gcloud_install():
#     with patch("termux_dev_setup.gcloud.run_command") as run, \
#          patch("termux_dev_setup.gcloud.check_command", side_effect=[True, False, True]), \
#          patch("termux_dev_setup.gcloud.Path") as MockPath, \
#          patch('builtins.open', mock_open()) as mock_file:

#         mock_path = MagicMock()
#         MockPath.return_value = mock_path

#         g.setup_gcloud()

#         run.assert_any_call("apt-get install -y apt-transport-https ca-certificates gnupg", check=True)

# def test_gcloud_already_installed():
#     with patch("termux_dev_setup.gcloud.run_command") as run, \
#          patch("termux_dev_setup.gcloud.check_command", return_value=True), \
#          patch('builtins.open', mock_open()):
#         g.setup_gcloud()
#         run.assert_not_called()
