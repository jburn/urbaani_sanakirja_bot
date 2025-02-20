import pytest
import main
from unittest.mock import MagicMock, patch

@patch('main.getenv', return_value=None)
def test_main_missing_token(mock_getenv):

    with pytest.raises(ValueError, match="Failed to open TOKEN file"):
        main.main()

    mock_getenv.assert_called_once_with("TELEGRAM_BOT_TOKEN")

@patch('main.getenv', return_value='expected')
@patch('main.ApplicationBuilder')
@patch('main.get_application_handlers', return_value=[])
def test_main_valid(mock_get_application_handlers, mock_app_builder, mock_getenv):
    mock_app = MagicMock()
    mock_app_builder.return_value.token.return_value.build.return_value = mock_app

    main.main()

    mock_getenv.assert_called_once_with("TELEGRAM_BOT_TOKEN")
    mock_get_application_handlers.assert_called_once()
    mock_app_builder.assert_called_once()
    
    mock_app.run_polling.assert_called_once_with(drop_pending_updates=True)
