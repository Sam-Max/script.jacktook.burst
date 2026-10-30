# -*- coding: utf-8 -*-
"""Regression tests for the upstream v0.0.100 integration (S1-S6).

Run: python3 -m unittest discover -s tests -v
Kodi/jacktook/elementum are stubbed; nothing here touches the network.
"""
import glob, importlib, importlib.util, json, os, py_compile, re, shutil, subprocess, sys, tempfile, types, unittest
from xml.etree import ElementTree

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(REPO, "resources", "site-packages")
DEFAULTS = {"timeout": "25", "max_retries": "1", "max_results": "10", "sort_by": "3", "proxy_type": "5",
            "proxy_use_type": "2", "proxy_port": "1080", "min_size": "0", "max_size": "100",
            "overwrite_anime_original_title": "1", "min_size_movies": "0", "max_size_movies": "100",
            "min_size_seasons": "0", "max_size_seasons": "100", "min_size_episodes": "0",
            "max_size_episodes": "100"}


def _mod(name, **attrs):
    m = types.ModuleType(name); m.__dict__.update(attrs); sys.modules[name] = m; return m


class Addon:
    def __init__(self, id=None): self.id = id or "script.jacktook.burst"
    def getAddonInfo(self, key):
        return {"id": "script.jacktook.burst", "name": "Jacktook Burst", "path": REPO,
                "icon": "icon.png", "profile": tempfile.gettempdir(), "version": "0.0.92",
                "author": "Sam-Max"}.get(key, "")
    def getSetting(self, id=None): return DEFAULTS.get(id, "")
    def setSetting(self, id=None, value=None): return None


class Dialog:
    def notification(self, *a, **k): return None
    def ok(self, *a, **k): return True


class DialogProgressBG:
    def create(self, *a, **k): return None
    def update(self, *a, **k): return None
    def close(self): return None
    def iscanceled(self): return False


class _BlockElementum:
    """Any residual `import elementum...` must fail loudly (S3)."""
    def find_spec(self, name, path=None, target=None):
        if name == "elementum" or name.startswith("elementum."):
            raise ImportError("blocked elementum import: %s" % name)
        return None


def setUpModule():
    def py(s): return s.decode("utf-8") if isinstance(s, bytes) else s
    _mod("kodi_six")
    _mod("kodi_six.xbmcaddon", Addon=Addon)
    _mod("kodi_six.xbmc", ISO_639_1="ISO_639_1", getInfoLabel=lambda n: "20.2",
         getLanguage=lambda fmt=None: "en", log=lambda *a, **k: None, translatePath=lambda p: p)
    _mod("kodi_six.xbmcgui", Dialog=Dialog, DialogProgressBG=DialogProgressBG)
    _mod("kodi_six.xbmcvfs", translatePath=lambda p: p)
    _mod("kodi_six.utils", py2_decode=py, py2_encode=py)
    for n in ("xbmc", "xbmcaddon", "xbmcgui", "xbmcvfs"):
        sys.modules[n] = sys.modules["kodi_six." + n]
    _mod("jacktook")
    _mod("jacktook.provider_base", Provider=type("Provider", (), {"register": lambda self: None}),
         ProviderResult=type("ProviderResult", (), {"__init__": lambda self, **kw: self.__dict__.update(kw)}))
    for p in (SITE, REPO):
        if p not in sys.path: sys.path.insert(0, p)
    sys.meta_path.insert(0, _BlockElementum())


def src(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as fh: return fh.read()


def py_files():
    files = [os.path.join(REPO, "burst.py")]
    for root, _d, names in os.walk(os.path.join(REPO, "burst")):
        if "icons" not in root:
            files += [os.path.join(root, n) for n in names if n.endswith(".py")]
    return sorted(files)


def po_files():
    return sorted(glob.glob(os.path.join(REPO, "resources", "language", "*", "strings.po")))


def entries(text):
    cur = {"ctx": None, "id": None, "str": None}
    for line in text.splitlines() + ['msgctxt #000']:
        m = re.match(r'msgctxt "#(\d+)"', line)
        if m:
            if cur["ctx"] is not None: yield cur["ctx"], cur["id"] or "", cur["str"] or ""
            cur = {"ctx": m.group(1), "id": None, "str": None}
        elif line.startswith("msgid "): cur["id"] = line[6:].strip('"')
        elif line.startswith("msgstr "): cur["str"] = line[7:].strip('"')


class S1UpstreamContent(unittest.TestCase):
    def test_legacy_modules_removed(self):
        for rel in ("burst/parser/HTMLParser.py", "burst/parser/markupbase.py", "burst/ordereddict.py",
                    "burst/navigation.py", "navigation.py", "burst/compat.py"):
            self.assertFalse(os.path.exists(os.path.join(REPO, rel)), rel)

    def test_stdlib_htmlparser_only(self):
        self.assertIn("from html.parser import HTMLParser", src("burst/parser/ehp.py"))
        hits = [f for f in py_files() if "HTMLParser" in src(os.path.relpath(f, REPO))]
        self.assertEqual(hits, [os.path.join(REPO, "burst/parser/ehp.py")])

    def test_no_imports_of_removed_modules(self):
        text = "".join(src(os.path.relpath(f, REPO)) for f in py_files())
        for name in ("ordereddict", "markupbase", "navigation", "compat"):
            self.assertNotRegex(text, r"(?m)^\s*(from|import)\s+.*\b%s\b" % name)

    def test_providers_json_counts(self):
        data = json.loads(src("burst/providers/providers.json"))
        self.assertEqual(len(data), 84)
        self.assertEqual(sum(1 for v in data.values() if v.get("enabled")), 61)

    def test_catalogs_carry_upstream_ids(self):
        for po in po_files():
            ids = set(re.findall(r'msgctxt "#(\d+)"', open(po, encoding="utf-8").read()))
            for wanted in ("32124", "32141", "32158", "32171"):
                self.assertIn(wanted, ids, "%s lacks #%s" % (po, wanted))


class S2ForkFixes(unittest.TestCase):
    def setUp(self):
        self.p = json.loads(src("burst/providers/providers.json"))

    def test_eztv_keywords_have_no_literal_quotes(self):
        for key in ("anime_keywords", "season_keywords", "tv_keywords"):
            self.assertNotIn('"', self.p["eztv"][key], key)
            self.assertNotIn("'", self.p["eztv"][key], key)

    def test_yts_base_url_uses_bz(self):
        self.assertTrue(self.p["yts"]["base_url"].startswith("https://yts.bz/"))

    def test_bitsearch_has_headers(self):
        self.assertIn("bitsearch.to", self.p["bitsearch"]["headers"])
        self.assertIn("Referer", self.p["bitsearch"]["headers"])

    def test_provider_field_has_no_color_tags(self):
        self.assertIn('"provider": definition[\'name\'],', src("burst/provider.py"))
        self.assertNotIn("[COLOR %s]", src("burst/provider.py"))

    def test_silent_flag_reaches_payload(self):
        spec = importlib.util.spec_from_file_location("burst_entry_silent", os.path.join(REPO, "burst.py"))
        entry = importlib.util.module_from_spec(spec); spec.loader.exec_module(entry)
        self.assertFalse(entry.movie_payload("tt1", "T", "", 1999)["silent"])
        self.assertTrue(entry.movie_payload("tt1", "T", "", 1999, silent=True)["silent"])
        self.assertTrue(entry.episode_payload("tt1", "T", 1, 2, "", 1999, silent=True)["silent"])

    def test_titles_are_normalized(self):
        spec = importlib.util.spec_from_file_location("burst_entry", os.path.join(REPO, "burst.py"))
        entry = importlib.util.module_from_spec(spec); spec.loader.exec_module(entry)
        self.assertEqual(entry.movie_payload("tt1", "T", "", 1999)["titles"],
                         {"source": "T", "original": "T"})
        self.assertEqual(entry.episode_payload("tt1", "T", 1, 2, {"EN": "E"}, "")["titles"], {"en": "E"})


class S3NoElementumProvider(unittest.TestCase):
    def test_no_elementum_provider_imports(self):
        targets = py_files() + [os.path.join(REPO, "resources", "site-packages", "antizapret.py")]
        for f in targets:
            self.assertNotIn("elementum.provider", src(os.path.relpath(f, REPO)), f)

    def test_all_modules_import_without_elementum(self):
        mods = []
        for f in py_files():
            rel = os.path.relpath(f, REPO)[:-3].replace(os.sep, ".")
            mods.append(rel[:-9] if rel.endswith(".__init__") else rel)
        failures = []
        for m in sorted(set(mods)):
            try: importlib.import_module(m)
            except Exception as exc: failures.append((m, repr(exc)))
        self.assertEqual(failures, [])
        self.assertEqual([k for k in sys.modules if k.startswith("elementum")], [])

    def test_antizapret_uses_stdlib_logging(self):
        self.assertIn("import logging", src("resources/site-packages/antizapret.py"))
        self.assertIn("logging.getLogger", src("resources/site-packages/antizapret.py"))


class S4Metadata(unittest.TestCase):
    def test_addon_xml(self):
        root = ElementTree.parse(os.path.join(REPO, "addon.xml")).getroot()
        self.assertEqual(root.get("id"), "script.jacktook.burst")
        self.assertRegex(root.get("version"), r"^\d+\.\d+\.\d+$")
        imports = {e.get("addon"): e.get("version") for e in root.iter() if e.tag == "import"}
        self.assertEqual(imports.get("xbmc.python"), "3.0.1")
        for addon in ("plugin.video.jacktook", "script.module.kodi-six",
                      "script.module.requests", "script.module.pycryptodome"):
            self.assertIn(addon, imports)
        self.assertNotIn("script.module.future", imports)

    def test_requirements_have_no_future(self):
        self.assertNotIn("future", [l.strip() for l in src("requirements.txt").splitlines() if l.strip()])

    def test_settings_xml_references_fork_addon(self):
        xml = src("resources/settings.xml"); ElementTree.fromstring(xml)
        self.assertIn("script.jacktook.burst", xml)
        self.assertNotIn("script.elementum.burst", xml)

    def test_catalog_msgids_say_jacktook(self):
        for po in po_files():
            for ctx, msgid, _s in entries(open(po, encoding="utf-8").read()):
                self.assertNotIn("elementum", msgid.lower(), "%s #%s" % (po, ctx))

    def test_catalog_headers_name_jacktook_addon(self):
        # S4 "language catalogs say Jacktook" - RED: 17 headers keep script.elementum.burst.
        for po in po_files() + [os.path.join(REPO, "resources", "language", "messages.pot")]:
            head = open(po, encoding="utf-8").read().splitlines()[:4]
            self.assertTrue(any("script.jacktook.burst" in l for l in head if l.startswith("#")),
                            "%s header still names Elementum" % po)

    def test_settings_conditions_reference_existing_neighbours(self):
        # Removing the Elementum proxy settings shifted relative indices; Kodi then
        # logs "cannot reference setting ... in another category" for every bad ref.
        root = ElementTree.parse(os.path.join(REPO, "resources", "settings.xml")).getroot()
        for category in root.iter("category"):
            settings = category.findall("setting")
            for index, setting in enumerate(settings):
                for attr in ("enable", "visible"):
                    condition = setting.get(attr) or ""
                    for match in re.finditer(r"eq\(\s*(-?\d+)\s*,", condition):
                        target = index + int(match.group(1))
                        self.assertTrue(0 <= target < len(settings),
                                        "%r %s=%r references out-of-range index %d"
                                        % (setting.get("id") or setting.get("label"), attr, condition, target))

    def test_spanish_auto_timeout_translation(self):
        # S4 regression: #32124 msgstr reverted to "elementum" by the re-baseline (was "jacktook").
        po = os.path.join(REPO, "resources", "language", "Spanish", "strings.po")
        for ctx, _i, msgstr in entries(open(po, encoding="utf-8").read()):
            if ctx == "32124":
                self.assertNotIn("elementum", msgstr.lower())
                self.assertIn("jacktook", msgstr.lower())


def _upstream_ref_available():
    return subprocess.run(["git", "-C", REPO, "rev-parse", "--verify", "elementum/master"],
                          capture_output=True, text=True).returncode == 0


@unittest.skipUnless(_upstream_ref_available(), "elementum/master ref not available in this clone")
class S5MergeCommit(unittest.TestCase):
    def test_upstream_is_merged_into_history(self):
        git = ["git", "-C", REPO]
        merges = subprocess.check_output(git + ["rev-list", "--merges", "-n1", "HEAD"], text=True).split()
        self.assertTrue(merges, "no merge commit in history")
        self.assertEqual(subprocess.check_output(git + ["rev-parse", merges[0] + "^2"], text=True).strip(),
                         subprocess.check_output(git + ["rev-parse", "elementum/master"], text=True).strip())


class S6Verification(unittest.TestCase):
    def test_all_python_compiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            for f in py_files():
                py_compile.compile(f, cfile=os.path.join(tmp, os.path.basename(f) + "c"), doraise=True)

    def test_xml_parses(self):
        for rel in ("addon.xml", "resources/settings.xml"):
            ElementTree.parse(os.path.join(REPO, rel))

    def test_generate_settings_is_a_fixed_point(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "resources")); os.makedirs(os.path.join(tmp, "burst", "providers"))
            shutil.copyfile(os.path.join(REPO, "resources", "settings.xml"), os.path.join(tmp, "resources", "settings.xml"))
            shutil.copyfile(os.path.join(REPO, "burst", "providers", "providers.json"),
                            os.path.join(tmp, "burst", "providers", "providers.json"))
            with open(os.path.join(REPO, "resources", "settings.xml"), "rb") as fh: expected = fh.read()
            subprocess.run([sys.executable, os.path.join(REPO, "scripts", "generate_settings.py")],
                           cwd=tmp, check=True, capture_output=True)
            with open(os.path.join(tmp, "resources", "settings.xml"), "rb") as fh:
                self.assertEqual(fh.read(), expected)

    def test_smoke_definitions_and_queries(self):
        import burst.burst as burst, burst.filtering as filtering, burst.providers.definitions as definitions
        self.assertEqual(len(definitions.definitions), 84)
        self.assertEqual(burst.append_headers("magnet:x", {"a": "b"}), "magnet:x|a=b")
        f = filtering.Filtering()
        f.use_episode("eztv", {"imdb_id": "tt0944947", "title": "Game of Thrones",
                               "titles": {"source": "Game of Thrones", "original": "Game of Thrones"},
                               "season": 1, "episode": 2, "year": 2011, "silent": True, "skip_auth": False})
        self.assertIn("eztvx.to", f.url)
        self.assertFalse([q for q in f.queries if "'" in q or '"' in q])
