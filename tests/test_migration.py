#!/usr/bin/env python3
import importlib.util, json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('migration',ROOT/'scripts/migrate.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class MigrationTest(unittest.TestCase):
 def test_dependencies(self):
  self.assertEqual(m.expand('zsh'),['common','oh-my-zsh','zsh'])
  self.assertNotIn('grub',m.expand('all'))
  self.assertNotIn('runtime',m.expand('all'))
  self.assertNotIn('gtk4',m.expand('all'))
 def test_relocate_text_and_symlink(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d); (p/'config').write_text('/home/source/.config/a')
   (p/'link').symlink_to('/home/source/.config/a')
   (p/'binary').write_bytes(b'\0/home/source')
   m.relocate(p,'/home/source','/home/target')
   self.assertEqual((p/'config').read_text(),'/home/target/.config/a')
   self.assertEqual(os.readlink(p/'link'),'/home/target/.config/a')
   self.assertEqual((p/'binary').read_bytes(),b'\0/home/source')
 def test_real_tex_copy_backup_restore(self):
  with tempfile.TemporaryDirectory(prefix='gnome migration ') as d:
   target=Path(d); original=target/'.config/shell/tex'
   original.mkdir(parents=True);(original/'keep.txt').write_text('original')
   cmd=[sys.executable,'-B',str(ROOT/'scripts/migrate.py'),'apply','tex','--target-home',d]
   result=subprocess.run(cmd,check=True,capture_output=True,text=True)
   self.assertFalse((target/'.local').exists())
   subprocess.run(cmd+['--execute'],check=True,capture_output=True,text=True)
   self.assertTrue((original/'latexcompile-simple.sh').exists())
   self.assertFalse((original/'keep.txt').exists())
   index=next((target/'.local/state/gnome-migrate').glob('*/restore.json'))
   subprocess.run([sys.executable,'-B',str(ROOT/'scripts/migrate.py'),'restore','--backup',str(index),'--execute'],check=True,capture_output=True,text=True)
   self.assertEqual((original/'keep.txt').read_text(),'original')
   self.assertFalse((original/'latexcompile-simple.sh').exists())
 def test_reject_unknown_component(self):
  with self.assertRaises(RuntimeError):m.expand('../bad')
 def test_distro_package_plans(self):
  source=(ROOT/'scripts/bootstrap.sh').read_text()
  for distro,expected in [('fedora','dnf'),('ubuntu','apt-get'),('debian','apt-get'),('arch','pacman'),('opensuse','zypper')]:
   with self.subTest(distro=distro), tempfile.TemporaryDirectory() as d:
    script=Path(d)/'bootstrap.sh'
    script.write_text(source.replace('. /etc/os-release', 'ID='+distro+'; ID_LIKE='))
    result=subprocess.run(['sh',str(script),'rime'],env={**os.environ,'DO':'0'},capture_output=True,text=True,check=True)
    self.assertIn(expected,result.stdout)
    self.assertIn('fcitx5-rime',result.stdout)
    if distro=='fedora': self.assertIn('librime-lua',result.stdout)
    if distro in ['ubuntu','debian']: self.assertIn('librime-plugin-lua',result.stdout)
 def test_windows_font_snapshot(self):
  source=ROOT/'payload/fonts/home/.local/share/fonts/Microsoft'
  self.assertEqual(sum(1 for p in source.rglob('*') if p.is_file()),217)
  result=subprocess.run([sys.executable,str(ROOT/'scripts/migrate.py'),'apply','windows-fonts'],capture_output=True,text=True,check=True)
  self.assertIn('.local/share/fonts/Microsoft',result.stdout)
  self.assertNotIn('/usr/share/fonts',result.stdout)
 def test_shell_syntax(self):
  for p in (ROOT/'scripts').glob('*.sh'): subprocess.run(['sh','-n',str(p)],check=True)
if __name__=='__main__': unittest.main(verbosity=2)
