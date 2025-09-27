#include <iostream>
#include <sstream>
// #include <string>
// #include <vector>

// using namespace std;

// class Pot {
// public:
//   int value;
//   vector<string> players;
// };

// class GameState {
// public:
//   size_t index_to_action;
//   size_t index_of_small_blind;
//   vector<string> players;
//   vector<string> player_cards;
//   vector<int> held_money;
//   vector<int> bet_money;
//   vector<string> community_cards;
//   vector<Pot> pots;
//   int small_blind;
//   int big_blind;
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

vector<int> split_into_ints(string &s) {
  vector<int> tokens;
  stringstream ss(s);

  string token;
  while (getline(ss, token, ' ')) {
    tokens.push_back(stoi(token));
  }

  return tokens;
}

void set_state_input(GameState &state) {
  string index_to_action_line;
  getline(cin, index_to_action_line);
  state.index_to_action = stoull(index_to_action_line);

  string index_of_small_blind_line;
  getline(cin, index_of_small_blind_line);
  state.index_of_small_blind = stoull(index_of_small_blind_line);

  string players_line;
  getline(cin, players_line);
  state.players = split(players_line);

  string players_cards_line;
  getline(cin, players_cards_line);
  state.player_cards = split(players_cards_line);

  string held_money_line;
  getline(cin, held_money_line);
  state.held_money = split_into_ints(held_money_line);

  string bet_money_line;
  getline(cin, bet_money_line);
  state.bet_money = split_into_ints(bet_money_line);

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
    p.value = stoi(pot_vec[0]);
    p.players = vector<string>(pot_vec.begin() + 1, pot_vec.end());

    pots.emplace_back(p);
  }
  state.pots = pots;

  string sb_line;
  getline(cin, sb_line);
  state.small_blind = stoi(sb_line);

  string bb_line;
  getline(cin, bb_line);
  state.big_blind = stoi(bb_line);
}

int main() {
  GameState state;

  set_state_input(state);

  // where the all the code happens!
  cout << bet(state) << endl;
}