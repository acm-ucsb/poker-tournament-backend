#include <string>
#include <vector>

using namespace std;

class Pot {
public:
  double value;
  vector<string> players;
};

class GameState {
public:
  vector<string> players;
  vector<string> player_cards;
  vector<double> held_money;
  vector<double> bet_money;
  vector<string> community_cards;
  vector<Pot> pots;
  string current_round;
};

// DO NOT CHANGE ABOVE CODE OR FUNCTION SIGNATURE ELSE YOUR CODE WILL NOT RUN!
// except... some libraries can be imported

int bet(GameState &state) { return 0; }