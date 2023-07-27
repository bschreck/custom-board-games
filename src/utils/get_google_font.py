from github import Auth
from github import Github
from dotenv import load_dotenv
import os
load_dotenv()


# TODO dataclass with optionals
class Font:
    def __init__(
        self, 
        name,
        reponame="google/fonts",
        path_prefix="ofl"
    ):
        self.name = name
        self.path_prefix = path_prefix
        self.reponame = reponame
        self.modifiers = ['regular', 'bold', 'semibold', 'italic']
        self.parse_dir()

    @property
    def github_client(self):
        auth = Auth.Token(os.getenv('GITHUB_TOKEN'))
        return Github(auth=auth)

    @property
    def path(self):
        return os.path.join(self.path_prefix, self.name)

    @property
    def all_files(self):
        return set([self.main] + [getattr(self, modif) for modif in self.modifiers
                if getattr(self, modif, None)])

    @property
    def repo(self):
        return self.github_client.get_repo(self.reponame)

    def download_files(self, dirname):
        os.makedirs(dirname, exist_ok=True)
        for fname in self.all_files:
            contents = self.repo.get_contents(os.path.join(self.path, fname))
            # TODO use Path object
            os.makedirs(os.path.join(dirname, self.name), exist_ok=True)
            with open(os.path.join(dirname, self.name, fname), "wb") as f:
                f.write(contents.decoded_content)

    def parse_dir(self):
        # TODO: this logic should just go in Font
        repo = self.github_client.get_repo("google/fonts")
        contents = repo.get_contents(self.path)
        ttfs = [cf for cf in contents if cf.name.endswith(".ttf")]
        if len(ttfs) == 0:
            raise ValueError(f"Could not find any .ttf files in {self.name}")
        if len(ttfs) == 1:
            self.main = ttfs[0].name
            return
        self.main = ttfs[0].name
        for cf in ttfs:
            for modif in ["regular", "bold", "semibold", "italic"]:
                if modif in cf.name.lower():
                    setattr(self, modif, cf.name)
                    if modif == "regular":
                        self.main = cf.name
    
        
if __name__ == '__main__':
    font = Font("abeezee")
    font.download_files("fonts")