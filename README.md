# <img src="web/src/assets/favicon.svg" height=30> Last Translation Benchmark

This platform gathers inputs (text, video, audio, images, documents) that are challenging for modern machine translation systems.
Contributors submit these inputs alongside machine translation outputs and a verification rule.
With 10 approved submissions, contributors are eligible for inclusion in the upcoming research publication.

There are three user roles:
- **Contributor** suggests inputs (text, images, and speech), auto-translate them, defines a verification method, and submits.
- **Reviewer** browses pending submissions and returns, accepts, or comments.
- **Admin** with the ability to create and modify users.
Each account is associated with a magic link that can be used to login from anywhere.

If you're interested in contributing, register at [last-translation-benchmark.vilda.net](https://last-translation-benchmark.vilda.net).
Make sure you read the instructions beforehand.

> Example from English to Czech translation: \
> **Source**: "_what's the difference between jail and prison?_" \
> **Translation (Google Translate)**: "_jaký je rozdíl mezi vězením a vězením?_" \
> **Translation (Human)**: "_jaký je rozdíl mezi vazební věznicí a vězením?_" \
> **Verification rule**: "_The words for the "jail" and "prison" shouldn't be identical."_

<img width="1000" alt="Last Translation Benchmark poster" src="https://github.com/user-attachments/assets/f0971f5c-fc95-4d48-9f13-a01934b4913d" />

## Development

```bash
# requires python >=3.12, node >= 20
npm install --prefix web
npm run build --prefix web/
# use this one when developing
pip install -e ".[dev]" && pre-commit install -c .github/.pre-commit-config.yaml
# use this one when not developing
pip install -e .
# prints login URLs
python3 server
```

The `server/` contains source code for the server.
The `web/` is the frontend code (TypeScript) which, when built, goes to `server/static/` to be served by the server.

You can specify the `--host`, `--port` and `--host-public` arguments when starting the server. 
The last is used to show the login URLs.

### Environment variables

Create `config.toml` based on `config.template.toml`
- `CONTRIBUTOR_QUOTA_DEFAULT` default "credits" for new users
- `DB_PATH` path to the persistent database file (will be created automatically)
- `EMAIL_*` configuration of email sending

Some API services need API keys:
- `OPENROUTER_API_KEY`: enables real LLM translation and verification
- `LARA_API_ID` and `LARA_API_SECRET`: enables Lara API-based translation
- `GOOGLE_TRANSLATE_API_KEY`: enables API-based Google Translate


### Instructions

The instructions in [web/src/assets/instructions.html](web/src/assets/instructions.html) are based on upstream document written in Typst and should not be edited locally in this repo.

## License

The source code in this repository is licensed under [MIT](LICENSE), and the data under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.en).

## Contributing

We welcome bugreports, hands-on, and research contributions.
AI-generated PRs are fine as long as you verify everything and take ownership of the changes.
This effort is organized by a collective of researchers from ETH Zurich, JHU, CUNI, UvA, KIT, and many others.
Reach out to [last-translation-benchmark@vilda.net](mailto:last-translation-benchmark@vilda.net) with inquiries.
Please do not reach out about the status of your pending submissions.
To speed up the review process, you can invite other speakers of your languages who can review your submissions or nominate yourself to be a reviewer.


## Citation

The Last Translation Benchmark is still in preparation.
If you need to cite this project, please use this temporary BibTeX:
```bibtex
@misc{last-translation-benchmark,
title={Last Translation Benchmark},
author={Vilém Zouhar and Niyati Bafna and Maike Züfle and Patrícia Schmidtová and Bhavitvya Malik and Sara Rajaee and Leshem Choshen and Gabriele Sarti and Orfeas Menis Mastromichalakis and Jan Niehues and Mukund Choudhary and Michelle Wastl and Pinzhen Chen and Alon Lavie and Ondřej Bojar and Sara Papi and Jannis Vamvas and Ona de Gibert and Sowmya Vajjala and Nils Rehlinger and Kranti and Hend Al-Khalifa and Malik Marmonier and Fred Philippy and Dominik Macháček and Vaisakhi Mishra and Fabian Retkowski and Cristina España-Bonet and Venkata Prasanth Kumar Gummadi and Maria Carmen Staiano and Wafa Aissa and Kaiser Sun and Avantica Vempati and Andrés Jerez and Dipankar Srirag and Lukas Edman and Hanna Yukhymenko and Silvia Casola and Javier García Gilabert and Maria Lymperaiou and Vitalii Babenko and Yihong Liu and Ruta Binkyte and Jagannathan Ramanujam and Sina Ahmadi and Philipp Mondorf and Zuzana Nadova and Eliya Habba and Valentin Scourneau and Marius Huber and Sangwon Ryu and Linh Vu and Jean Maillard and Shaomu Tan and Paul Gavrikov and Fatima Haouari and Christian Hoang and Heejin Do and Xiaochuang Yuan and Manar Ali and Sergey Troshin and Sophia Conrad and Luis Lara and David Kaczér and Carlos Hinojosa and Anumit Garg and Andrea Gregor de Varda and Mykola Haltiuk and Raoyuan Zhao and Ngoc Quynh Tram Do and Marco Gaido and Lena Libon and Koel Dutta Chowdhury and Tim Graf and Sankalan Pal Chowdhury and Yolanda Xavier and Raia Abu Ahmad and Karen Sanchez and Joseph Attieh and Enzo Doyen and Chenyi Zhao and Benoît Sagot and Antoine Taroni and Rachel Bawden and Samuel Simko and Daban Q. Jaff and Ayush Sunil Munot and Aviral Nigam and Alex Flückiger and Kamile Dementaviciute and Jonathan Tonglet and Jirui Qi and Hassan Soliman and Antonia Karamolegkou and Kaustubh Dhole and Juan Daniel Cuervo Villa and Yi Fan and Priyaranjan Pattnayak and Marta Punsola Munárriz and Guy Kaplan and Clara Lachenmaier and Chuang Han and Blanka Kövér and Beatrice Savoldi and Bastian Bunzeck and Amir Hossein Yari and Vatsal Venkatkrishna and Peng Cui and Mateusz Lango and Jana Massoud and Dzmitry Kuzmin and David Stap and Yu Fan and Zhengxiang Wang and Ondrej Klejch and Deep Shah and Beni Egressy and Ahrii Kim and Tommaso Cerruti and Kazuki Egashira and Isabelle Caroline Rose Cretton and Bo Chen and Anna Sokol and Jingwei Ni and Evgeniia Tokarchuk and Ziyi Yang and Zaid Alyafeai and Yuxing Lu and Yang Tian and Xinzhou He and Seth Aycock and Sayuj Keerangatil and Ritwik Tiwari and Patricia Scheurer and Nathan Nowakowski and Minh Ngọc and Manuel Tuor and Kristýna Onderková and Juri Opitz and Judith Sieker and Giuseppe Gallipoli and Fidel Rodríguez Velásquez and Farzad Shami and David Thulke and Shunta Asano and Nathaniel Berger and Yingqiang Gao and Thyra Krosness and Theresia Veronika Rampisela and Shubhashis Roy Dipta and Samuel Frontull and Rayyan Merchant and Rahul Seetharaman and R. Damanhuri and Pavel Stepachev and Nidhi Vaghela and Muhammad Ravi Shulthan Habibi and Maria Thedim and Jan Kocoń and Hongbin Na and Daniel Paleka and Börje F. Karlsson and Bowen Yi and Azmine Toushik Wasi and Avijit Thawani and Aishwarya Selvamurugan and Aina Garí Soler and Aicha Chorana and Aditya Bakshi and Aarush Sinha},
year={2026},
url={https://last-translation-benchmark.vilda.net/},
note={In preparation},
}
```