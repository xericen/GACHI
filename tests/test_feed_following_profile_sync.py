import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
API_SOURCE = (ROOT / "src/app/page.access/api.py").read_text(encoding="utf-8")
VIEW_SOURCE = (ROOT / "src/app/page.access/view.ts").read_text(encoding="utf-8")


class FeedFollowingProfileSyncTests(unittest.TestCase):
    def test_backend_exposes_persisted_following_authors(self):
        self.assertIn('def _followed_author_rows(user_id):', API_SOURCE)
        self.assertIn('community_action == "author_follows"', API_SOURCE)
        self.assertIn('following_authors=_followed_author_rows(user_id)', API_SOURCE)

    def test_feed_follow_updates_my_profile_list(self):
        self.assertIn("await this.loadMyProfileFollowing(false);", VIEW_SOURCE)
        self.assertIn("this.applyMyProfileFollowing(response.data.following_authors);", VIEW_SOURCE)
        self.assertIn("community_action: 'author_follows'", VIEW_SOURCE)

    def test_profile_unfollow_uses_the_same_persisted_action(self):
        self.assertIn("private profilePersonAuthorId(person: any)", VIEW_SOURCE)
        self.assertIn("community_action: 'author_follow'", VIEW_SOURCE)
        self.assertIn("author_id: authorId", VIEW_SOURCE)


if __name__ == "__main__":
    unittest.main()
