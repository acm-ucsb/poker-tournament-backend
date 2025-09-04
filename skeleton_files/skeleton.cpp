#include <iostream>
#include <sstream>

// #include <string>
// #include <vector>

// using namespace std;

// class Pot {
// public:
//   double value;
//   vector<string> players;
// };

// class GameState {
// public:
//   vector<string> players;
//   vector<string> player_cards;
//   vector<double> held_money;
//   vector<double> bet_money;
//   vector<string> community_cards;
//   vector<Pot> pots;
//   string current_round;
// };

// ================================ //
// ACTUAL BOT CODE FUNCTION HERE!!! //
// ================================ //
//%insert%//

vector<string> split(string &s) {
  vector<string> tokens;
  stringstream ss(s);

  string token;
  while (getline(ss, token, ' ')) {
    tokens.push_back(token);
  }

  return tokens;
}

vector<double> split_into_doubles(string &s) {
  vector<double> tokens;
  stringstream ss(s);

  string token;
  while (getline(ss, token, ' ')) {
    tokens.push_back(stod(token));
  }

  return tokens;
}

void set_state_input(GameState &state) {
  string players_line;
  getline(cin, players_line);
  state.players = split(players_line);

  string players_cards_line;
  getline(cin, players_cards_line);
  state.player_cards = split(players_cards_line);

  string held_money_line;
  getline(cin, held_money_line);
  state.held_money = split_into_doubles(held_money_line);

  string bet_money_line;
  getline(cin, bet_money_line);
  state.bet_money = split_into_doubles(bet_money_line);

  string community_cards_line;
  getline(cin, community_cards_line);
  state.community_cards = split(community_cards_line);

  string num_pots_line;
  getline(cin, num_pots_line);
  int num_pots = stoi(num_pots_line);

  vector<Pot> pots;
  for (int i = 0; i < num_pots; i++) {
    string pot_line;
    getline(cin, pot_line);
    vector<string> pot_vec = split(pot_line);

    Pot p;
    p.value = stod(pot_vec[0]);
    p.players = vector<string>(pot_vec.begin() + 1, pot_vec.end());

    pots.emplace_back(p);
  }
  state.pots = pots;

  getline(cin, state.current_round);
}

int main() {
  GameState state;

  set_state_input(state);

  // where the all the code happens!
  cout << bet(state) << endl;
}