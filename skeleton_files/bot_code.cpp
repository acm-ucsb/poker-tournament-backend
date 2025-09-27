#include <cstddef>
#include <string>
#include <vector>

using namespace std;

class Pot {
public:
  int value;
  vector<string> players;
};

class GameState {
public:
  size_t index_to_action;
  size_t index_of_small_blind;
  vector<string> players;
  vector<string> player_cards;
  vector<int> held_money;
  vector<int> bet_money;
  vector<string> community_cards;
  vector<Pot> pots;
  int small_blind;
  int big_blind;
};

// DO NOT CHANGE ABOVE CODE OR FUNCTION SIGNATURE ELSE YOUR CODE WILL NOT RUN!
// except... some libraries can be imported

int bet(GameState &state) { return 0; }