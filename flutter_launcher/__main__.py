import os
submodule = os.environ.get("submodule", "")

if submodule == "flutter":
    from flutter_launcher.flutter import main
    main()
