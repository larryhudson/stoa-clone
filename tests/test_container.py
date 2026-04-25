from app.container import build_container


def test_build_container_uses_pi_bin_environment_override(monkeypatch, tmp_path):
    monkeypatch.setenv("PI_BIN", "/custom/pi")

    container = build_container(base_dir=tmp_path)

    assert container.agent_runtime.command == [
        "/custom/pi",
        "--mode",
        "rpc",
        "--no-session",
    ]
