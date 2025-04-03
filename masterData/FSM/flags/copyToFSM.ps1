ls $env:LOCALAPPDATA\FSManagerUiShell\app-* | % { $fsm_app_dir = $_.fullname }
echo "FSM appdata directory: $fsm_app_dir"
mkdir "$fsm_app_dir\Flags"
ls *.png | % { echo "Copying $_ to $fsm_app_dir\Flags"; cp $_.fullname $fsm_app_dir\Flags }
